from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import List, Optional, Union
from opengsq.protocol_base import ProtocolBase
from opengsq.exceptions import InvalidPacketException
from opengsq.responses.trackmania_nations import ServerInfo


@dataclass
class SrvInfo:
    """Repräsentiert die wichtigsten Informationen eines #SRV#-Pakets."""
    variant: str
    server_name: Optional[str]
    environment: Optional[str]
    comment: Optional[str]
    maps: List[str] = field(default_factory=list)
    max_players: Optional[int] = None
    current_players: Optional[int] = None
    host_id: Optional[str] = None
    raw_strings: List[str] = field(default_factory=list, repr=False)


class TrackmaniaNations(ProtocolBase):
    """
    Trackmania Nations Protocol Implementation
    Basiert auf Reverse-Engineering der #SRV# Server-Announcement-Payloads
    """

    @property
    def full_name(self) -> str:
        return "Trackmania Nations Protocol"

    # Standard Trackmania Nations port
    DEFAULT_PORT = 2350

    # TCP packets as specified
    _PACKET_1 = bytes.fromhex("0e000000820399f895580700000008000000")
    _PACKET_2 = bytes.fromhex("1200000082033bd464400700000007000000d53d4100")

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)

    async def get_info(self) -> ServerInfo:
        """
        Retrieves server information by sending the two TCP packets in sequence.
        
        :return: A ServerInfo object containing server information
        :raises InvalidPacketException: If the response doesn't contain #SRV# marker
        """
        # Connect via TCP
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), 
                timeout=self._timeout
            )
        except (OSError, asyncio.TimeoutError) as e:
            raise InvalidPacketException(f"Failed to connect to {self._host}:{self._port}: {e}")

        try:
            # Send first packet
            writer.write(self._PACKET_1)
            await writer.drain()

            # Wait 200ms as specified
            await asyncio.sleep(0.2)

            # Send second packet
            writer.write(self._PACKET_2)
            await writer.drain()

            # Read response
            response_data = await asyncio.wait_for(
                reader.read(4096), 
                timeout=self._timeout
            )

            # Validate response contains #SRV# marker
            if b'#SRV#' not in response_data:
                raise InvalidPacketException(f"Response does not contain #SRV# marker. Got {len(response_data)} bytes.")

            # Parse using the new serializer
            srv_info = self.parse_srv_payload(response_data)
            
            # Convert to ServerInfo format
            return ServerInfo(
                name=srv_info.server_name or "Unknown",
                map=srv_info.maps[0] if srv_info.maps else "Unknown",
                players=srv_info.current_players or 0,
                max_players=srv_info.max_players or 0,
                game_mode="Unknown",
                password_protected=srv_info.variant in ['p', 'x'],
                version=None,
                environment=srv_info.environment,
                comment=srv_info.comment,
                server_login="",
                pc_guid=srv_info.host_id,
                time_limit=0,
                nb_laps=0,
                spectator_slots=0,
                build_number=0,
                private_server=srv_info.variant in ['p', 'x'],
                ladder_server=srv_info.variant in ['s', 'x'],
                status_flags=0,
                challenge_crc=0,
                public_ip="",
                local_ip="",
                raw_data=response_data.hex()
            )

        except asyncio.TimeoutError:
            raise InvalidPacketException("Timeout while waiting for server response")
        finally:
            writer.close()
            await writer.wait_closed()

    def parse_srv_payload(self, payload: Union[str, bytes, bytearray]) -> SrvInfo:
        """Zerlegt ein Trackmania-Server-Paket (#SRV#) und liefert ein SrvInfo-Objekt.

        Argumente
        ---------
        payload
            Hex-String (ohne Leerzeichen) *oder* Roh-Bytes.
        """
        # ASCII regex für längere Sequenzen
        _ASCII_RE = re.compile(rb"[ -~]{3,}")
        _MAP_RE = re.compile(r"^[A-Z]\d{2}-")

        # 1) Eingabe normieren
        if isinstance(payload, str):
            data = bytes.fromhex(payload.strip())
        else:
            data = bytes(payload)

        # 2) Header suchen (#SRV#X)
        header_idx = data.find(b"#SRV#")
        if header_idx == -1 or header_idx + 5 >= len(data):
            raise ValueError("Kein #SRV#-Header im Payload gefunden")

        variant_byte = data[header_idx + 5: header_idx + 6]
        variant = variant_byte.decode("ascii", errors="ignore") or "?"

        # 3) ASCII-Sequenzen extrahieren (sowohl Regex als auch Length-Prefixed)
        ascii_strings = [m.decode("ascii") for m in _ASCII_RE.findall(data)]
        
        # ERWEITERT: Extrahiere auch Length-Prefixed Strings für bessere Genauigkeit
        length_prefixed_strings = self._extract_length_prefixed_strings(data, header_idx)

        # 4) Korrigierte Zuordnung der Strings basierend auf MCP-Analyse
        # Suche nach #SRV# Header (mit oder ohne Variant)
        header_str_index = -1
        for i, s in enumerate(ascii_strings):
            if s.startswith("#SRV#"):
                header_str_index = i
                break
        
        # KORREKTUR basierend auf MCP-Analyse:
        # Position 0: Host-ID (z.B. "dgn-deb", "PC-ce9b0c") 
        # Position 1: "#SRV#" oder "#SRV#P"
        # Position 2: Echter Servername (z.B. "Organich", "BananeBongo")
        # Position 3: Environment (z.B. "Stadium", "Stadiumt")
        # Position 4: Comment/weitere Infos
        
        if header_str_index >= 0:
            # Host-ID ist der String VOR #SRV# (Position header_str_index - 1)
            host_id = ascii_strings[header_str_index - 1] if header_str_index >= 1 else None
            
            # VERBESSERT: Verwende Length-Prefixed Strings für dynamische Erkennung
            if length_prefixed_strings:
                # Vollständig dynamische Identifikation basierend nur auf Struktur
                server_name = None
                environment = None
                
                # SCHRITT 1: Erkenne Environment zuerst
                for string in length_prefixed_strings:
                    if self._is_environment_name(string.lower()) and not environment:
                        if string.lower().startswith('stad'):
                            environment = "Stadium"
                        elif string.lower() == 'island':
                            environment = "Island"
                        elif string.lower() == 'bay':
                            environment = "Bay"
                        elif string.lower() == 'coast':
                            environment = "Coast"
                        else:
                            environment = string
                        break
                
                # SCHRITT 2: Erkenne Server-Name (nicht Environment, nicht Map)
                for string in length_prefixed_strings:
                    if (not self._is_environment_name(string.lower()) and
                        not re.match(r'^[A-Z]\d{2,3}-', string) and
                        len(string) >= 3):
                        if not server_name or len(string) > len(server_name):
                            server_name = string
                
                # Fallback auf ASCII-Parsing für Comment
                comment = ascii_strings[header_str_index + 3] if header_str_index + 3 < len(ascii_strings) else None
                
                # ZUSÄTZLICHER FALLBACK: Wenn kein Server-Name in Length-Prefixed Strings gefunden wurde,
                # prüfe die ASCII-Strings mit strukturbasierten Filtern
                if not server_name:
                    for string in ascii_strings:
                        if (self._is_potential_server_name(string) and 
                            not self._is_environment_name(string.lower())):
                            server_name = string
                            break
                
                # ERWEITETER FALLBACK: Wenn der Length-Prefixed Name zu kurz ist (< 5 Zeichen),
                # schaue ob es einen längeren Namen in den ASCII-Strings gibt
                if server_name and len(server_name) < 5:
                    for string in ascii_strings:
                        if (self._is_potential_server_name(string) and 
                            not self._is_environment_name(string.lower()) and
                            len(string) > len(server_name)):
                            server_name = string
                            break
            else:
                # Fallback auf ASCII-String-Methode mit strukturbasierten Filtern
                server_name = None
                environment = None
                comment = None
                
                # Finde Server-Name und Environment in ASCII-Strings
                for i, string in enumerate(ascii_strings):
                    if i <= header_str_index:  # Überspringe Strings vor/bei #SRV#
                        continue
                        
                    if self._is_environment_name(string.lower()) and not environment:
                        environment = string
                    elif self._is_potential_server_name(string) and not server_name:
                        server_name = string
                    elif not comment and len(string) >= 4:
                        comment = string
                    
                    # Stoppe wenn alles gefunden
                    if server_name and environment and comment:
                        break
        else:
            # Fallback für unbekannte Struktur
            server_name = "Unknown"
            host_id = None
            environment = None
            comment = None
        maps = [s for s in ascii_strings if _MAP_RE.match(s)]

        # 5) Spielerzahlen abschätzen
        max_players, current_players = self._guess_player_counts(data, header_idx)

        return SrvInfo(
            variant=variant,
            server_name=server_name,
            environment=environment,
            comment=comment,
            maps=maps,
            max_players=max_players,
            current_players=current_players,
            host_id=host_id,
            raw_strings=ascii_strings,
        )

    def _guess_player_counts(self, data: bytes, header_pos: int) -> tuple[Optional[int], Optional[int]]:
        """Versucht max und current players aus den 64 Bytes vor header_pos zu lesen."""
        ints: List[int] = [
            int.from_bytes(data[o:o + 4], "little")
            for o in range(max(0, header_pos - 64), header_pos, 4)
        ]
        plausible = [x for x in ints if 0 < x <= 255]
        # Im beobachteten Paket fanden sich max- und current-Spieler als erste beiden kleinen Werte.
        if len(plausible) >= 2:
            return plausible[0], plausible[1]
        if len(plausible) == 1:
            return plausible[0], plausible[0]
        return None, None

    def _extract_length_prefixed_strings(self, data: bytes, start_pos: int) -> List[str]:
        """Vollständig dynamische Extraktion von Length-Prefixed Strings basierend auf Payload-Struktur.
        
        Analysiert die Bytes nach #SRV# und findet alle Length-Prefixed Strings ohne hardcodierte Namen.
        """
        strings = []
        
        # Erweiterte Suche nach #SRV#
        search_start = start_pos + 6
        search_end = min(start_pos + 80, len(data))
        
        # Sammle alle möglichen String-Kandidaten
        candidates = []
        
        for pos in range(search_start, search_end - 3):
            byte = data[pos]
            
            # Prüfe ob das ein plausibles Length-Byte ist (1-20 Zeichen)
            if 1 <= byte <= 20:
                # Teste verschiedene Offsets nach dem Length-Byte
                for offset in range(1, 5):
                    string_start = pos + offset
                    string_end = string_start + byte
                    
                    if string_end <= len(data):
                        string_bytes = data[string_start:string_end]
                        
                        # Prüfe ob alle Bytes druckbare ASCII-Zeichen sind
                        if all(32 <= b <= 126 for b in string_bytes):
                            try:
                                string = string_bytes.decode('ascii')
                                
                                # Strukturbasierte Validierung (ohne Namen-spezifische Regeln)
                                if self._is_structurally_valid_string(string):
                                    quality_score = self._calculate_structural_quality(string, pos, offset, byte)
                                    candidates.append({
                                        'string': string,
                                        'score': quality_score,
                                        'pos': pos,
                                        'offset': offset,
                                        'length': byte,
                                        'start': string_start,
                                        'end': string_end
                                    })
                            except UnicodeDecodeError:
                                pass
        
        # Sortiere nach Qualität und entferne Überlappungen
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        selected = []
        used_ranges = []
        
        for candidate in candidates:
            # Prüfe auf Überlappung
            overlaps = any(
                not (candidate['end'] <= used_start or candidate['start'] >= used_end)
                for used_start, used_end in used_ranges
            )
            
            if not overlaps and candidate['string'] not in selected:
                selected.append(candidate['string'])
                used_ranges.append((candidate['start'], candidate['end']))
                
                if len(selected) >= 4:  # Maximal 4 Strings
                    break
        
        return selected
    
    def _is_structurally_valid_string(self, string: str) -> bool:
        """Strukturbasierte Validierung ohne hardcodierte Namen."""
        # Mindestlänge
        if len(string) < 3:
            return False
            
        # Muss hauptsächlich alphabetisch sein
        alpha_count = sum(1 for c in string if c.isalpha())
        if alpha_count < 2:
            return False
            
        # Nicht nur Sonderzeichen
        special_count = sum(1 for c in string if not c.isalnum())
        if special_count > len(string) // 2:
            return False
            
        # Keine reinen Zahlen
        if string.isdigit():
            return False
            
        return True
    
    def _calculate_structural_quality(self, string: str, pos: int, offset: int, expected_length: int) -> float:
        """Berechnet Qualität basierend auf Struktur, nicht auf Namen."""
        score = 0.0
        
        # Length-Byte muss exakt stimmen
        if len(string) != expected_length:
            return 0.0
        
        # Längere Strings sind oft wichtiger (Server-Namen)
        score += len(string) * 0.2
        
        # Alphabetische Zeichen sind gut
        alpha_ratio = sum(1 for c in string if c.isalpha()) / len(string)
        score += alpha_ratio * 3.0
        
        # Nur bekannte Environment-Namen (fest im Spiel)
        if string.lower() in ['stadium', 'island', 'bay', 'coast']:
            score += 2.0
        elif string.lower().startswith('stad'):  # Stadium-Varianten
            score += 1.5
            
        # Kleinere Offsets sind wahrscheinlicher
        score -= offset * 0.1
        
        # Erste Strings im Payload sind oft wichtiger
        score -= pos * 0.001
        
        return score
    
    def _is_environment_name(self, string_lower: str) -> bool:
        """Prüft ob ein String ein bekanntes TrackMania Environment ist (fest im Spiel)."""
        return (string_lower in ['stadium', 'island', 'bay', 'coast'] or 
                string_lower.startswith('stad'))
    
    def _is_potential_server_name(self, string: str) -> bool:
        """Strukturbasierte Prüfung ob ein String ein potentieller Server-Name ist."""
        if len(string) < 3:
            return False
            
        # Filtere technische Strings
        if (string.startswith('#') or 
            string.startswith('PC-') or
            re.match(r'^[A-Z]\d{2,3}-', string)):  # Map-Namen
            return False
            
        # Filtere Host-IDs (lange Strings mit Bindestrichen)
        if '-' in string and len(string) > 8:
            return False
            
        # Muss hauptsächlich alphabetische Zeichen haben
        alpha_count = sum(1 for c in string if c.isalpha())
        if alpha_count < 3:
            return False
            
        # Nicht nur Sonderzeichen
        special_count = sum(1 for c in string if not c.isalnum())
        if special_count > len(string) // 2:
            return False
            
        return True



