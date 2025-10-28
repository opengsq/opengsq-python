from __future__ import annotations

import asyncio
import struct
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from opengsq.protocol_base import ProtocolBase
from opengsq.exceptions import InvalidPacketException
from opengsq.responses.trackmania_nations import ServerInfo


@dataclass
class TrackmaniaPayloadData:
    """Strukturierte Daten aus dem Trackmania Payload"""
    server_name: Optional[str] = None
    srv_type: Optional[str] = None
    environment: Optional[str] = None
    maps: List[str] = None
    players: Optional[int] = None
    max_players: Optional[int] = None
    game_mode: Optional[str] = None
    comment: Optional[str] = None
    raw_strings: List[str] = None

    def __post_init__(self):
        if self.maps is None:
            self.maps = []
        if self.raw_strings is None:
            self.raw_strings = []


class TrackmaniaNations(ProtocolBase):
    """
    Trackmania Nations Protocol Implementation
    Basiert auf MCP/Ghidra Reverse-Engineering

    MCP-Erkenntnisse:
    - Servername bei Position 0x27 mit 4-Byte Längen-Präfix (Little Endian)
    - #SRV# Marker mit 5-Byte Länge und Typ-Indikator
    - Drei Haupt-Typen: SRV#f (Float), SRV#s (String), SRV#p (Packet)
    - Strings verwenden 4-Byte Längen-Präfixe
    """

    @property
    def full_name(self) -> str:
        return "Trackmania Nations Protocol (MCP-Enhanced)"

    # Standard Trackmania Nations port
    DEFAULT_PORT = 2350

    # TCP packets (verifiziert)
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

            # Parse using MCP-based parser
            payload_data = self.parse_server_payload(response_data)

            # Convert to ServerInfo format
            # Die Namens-Logik in parse_server_payload hat bereits die richtigen Namen zugeordnet
            return ServerInfo(
                name=payload_data.server_name or "Unknown",  # Echter Server-Name (korrigiert in parse_server_payload)
                map=payload_data.maps[0] if payload_data.maps else "Unknown",
                players=payload_data.players or 0,
                max_players=payload_data.max_players or 0,
                game_mode=payload_data.game_mode or "Unknown",
                password_protected=payload_data.srv_type == 'p',
                version=None,
                environment=payload_data.environment,
                comment=payload_data.comment,  # PC-UID oder andere Info
                server_login="",
                pc_guid=payload_data.comment if payload_data.comment and payload_data.comment.startswith('PC-') else None,  # PC-UID
                time_limit=0,
                nb_laps=0,
                spectator_slots=0,
                build_number=0,
                private_server=payload_data.srv_type == 'p',
                ladder_server=payload_data.srv_type == 's',
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

    def parse_server_payload(self, data: bytes) -> TrackmaniaPayloadData:
        """
        Parst einen Server-Payload basierend auf MCP-Erkenntnissen.

        Args:
            data: Die Rohdaten des Payloads

        Returns:
            TrackmaniaPayloadData mit extrahierten Informationen
        """
        result = TrackmaniaPayloadData()

        # 1. String bei 0x27 extrahieren (kann PC-UID oder Server-Name sein, abhängig vom SRV-Typ)
        string_at_0x27 = None
        if len(data) >= 0x2b:  # 0x27 + 4 bytes für Länge
            string_at_0x27, _ = self._deserialize_string(data, 0x27)
            # Temporär speichern - wird später basierend auf SRV-Typ zugeordnet
            result.server_name = string_at_0x27

        # 2. #SRV# Marker und Typ finden
        srv_pos = data.find(b'#SRV#')
        if srv_pos != -1 and srv_pos + 5 < len(data):
            # Typ-Byte nach #SRV#
            srv_type_byte = data[srv_pos + 5]
            if srv_type_byte == 0x00:
                result.srv_type = 'null'
            elif chr(srv_type_byte).lower() in ['f', 's', 'p']:
                result.srv_type = chr(srv_type_byte).lower()
            else:
                result.srv_type = f'unknown_{srv_type_byte:02x}'

        # 3. MCP-basierte Challenge/Map-Namen Extraktion (mit SRV-Typ)
        challenge_name = self._extract_challenge_name(data, srv_pos, result.srv_type)
        if challenge_name:
            result.maps.append(challenge_name)

        # 4. Weitere Strings extrahieren für Environment, etc.
        strings = self._extract_all_strings(data)
        result.raw_strings = strings

        # 5. Spezifische Daten extrahieren
        for string in strings:
            # Fallback für Maps wenn MCP-Extraktion nichts fand
            if not result.maps and self._is_valid_challenge_name(string):
                result.maps.append(string)
            # Environment
            elif string.lower() in ['stadium', 'island', 'bay', 'coast']:
                result.environment = string.title()

        # 6. Spielerzahlen extrahieren (basierend auf Typ)
        player_data = self._extract_player_counts(data, srv_pos, result.srv_type)
        if player_data:
            result.players, result.max_players = player_data

        # 7. Game-Mode via MCP/Ghidra-Marker extrahieren (robust, ohne String-Heuristik)
        mode_name = self._extract_game_mode(data)
        if mode_name:
            result.game_mode = mode_name

        # 8. MCP-basierte korrekte Zuordnung basierend auf SRV-Typ
        if result.srv_type == 'p':
            # Private Server: 0x27 = PC-UID, echter Name in ASCII-Strings
            result.comment = string_at_0x27  # PC-UID

            # Finde echten Server-Namen aus ASCII-Strings
            potential_names = [s for s in strings if
                              len(s) >= 4 and
                              not s.startswith('PC-') and
                              s != result.environment and
                              not self._is_valid_challenge_name(s) and
                              not s.startswith('#') and
                              'lanparty' not in s.lower() and
                              'obstacle' not in s.lower()]  # Filter korrupte Namen

            if potential_names:
                potential_names.sort(key=len, reverse=True)
                result.server_name = potential_names[0]  # Längster = echter Server-Name

        elif result.srv_type == 'null' or result.srv_type is None:
            # Default/Null Server: Finde echten Server-Namen in ASCII-Strings
            # 0x27 könnte PC-UID oder Server-Name sein - prüfe Pattern

            # Finde potentielle Server-Namen (alphabetische Namen bevorzugt)
            potential_names = [s for s in strings if
                              3 <= len(s) <= 15 and  # Kurze, prägnante Namen
                              not s.startswith('PC-') and
                              not s.startswith('#') and
                              s != result.environment and
                              not self._is_valid_challenge_name(s) and
                              not any(kw in s.lower() for kw in ['stadium', 'lanparty', 'obstacle']) and
                              s.isalpha()]  # Nur alphabetische Namen (wie "Bruno")

            if potential_names:
                # Priorisiere kürzeste alphabetische Namen
                potential_names.sort(key=len)
                real_server_name = potential_names[0]

                # Wenn 0x27 String länger/anders ist, ist es wahrscheinlich PC-UID
                if string_at_0x27 and string_at_0x27 != real_server_name:
                    result.server_name = real_server_name
                    result.comment = string_at_0x27  # PC-UID/Login
                else:
                    result.server_name = string_at_0x27 or real_server_name
                    result.comment = None
            else:
                # Fallback: 0x27 als Server-Name
                result.server_name = string_at_0x27
                result.comment = None

        else:
            # Andere Server-Typen: Fallback zur alten Logik
            potential_names = [s for s in strings if
                              len(s) >= 3 and
                              s != result.environment and
                              not self._is_valid_challenge_name(s) and
                              not s.startswith('#')]

            if potential_names:
                potential_names.sort(key=len, reverse=True)
                longest = potential_names[0]
                if len(longest) > len(string_at_0x27 or ''):
                    result.server_name = longest
                    result.comment = string_at_0x27
                else:
                    result.comment = longest

        return result

    def _deserialize_string(self, data: bytes, offset: int) -> Tuple[Optional[str], int]:
        """
        Deserialisiert einen String mit 4-Byte Längen-Präfix (Little Endian).

        Args:
            data: Die Rohdaten
            offset: Start-Position

        Returns:
            Tuple aus (String oder None, Anzahl gelesener Bytes)
        """
        if offset + 4 > len(data):
            return None, 0

        # Länge lesen (4 Bytes, Little Endian)
        length = struct.unpack('<I', data[offset:offset+4])[0]

        # Plausibilitätsprüfung
        if length == 0 or length > 100 or offset + 4 + length > len(data):
            return None, 0

        # String lesen
        try:
            string_data = data[offset+4:offset+4+length]
            string = string_data.decode('utf-8', errors='replace')
            return string, 4 + length
        except:
            return None, 0

    def _extract_all_strings(self, data: bytes) -> List[str]:
        """
        Extrahiert alle lesbaren ASCII-Strings aus den Daten.

        Args:
            data: Die Rohdaten

        Returns:
            Liste der gefundenen Strings
        """
        strings = []
        current_string = bytearray()

        for byte in data:
            if 32 <= byte <= 126:  # Druckbare ASCII-Zeichen
                current_string.append(byte)
            else:
                if len(current_string) >= 3:  # Mindestens 3 Zeichen
                    try:
                        string = current_string.decode('ascii')
                        strings.append(string)
                    except:
                        pass
                current_string = bytearray()

        # Letzten String nicht vergessen
        if len(current_string) >= 3:
            try:
                string = current_string.decode('ascii')
                strings.append(string)
            except:
                pass

        return strings

    def _is_map_name(self, string: str) -> bool:
        """
        Prüft ob ein String ein Map-Name ist (striktere Typen, keine korrupten Suffixe).
        """
        import re
        allowed = r'(race|acrobatic|speed|endurance|platform|puzzle)'
        if re.match(rf'^[A-E]\d{{2}}-{allowed}$', string, re.IGNORECASE):
            return True
        if re.match(rf'^\d+-{allowed}$', string, re.IGNORECASE):
            return True
        return False

    def _extract_player_counts(self, data: bytes, srv_pos: int, srv_type: str) -> Optional[Tuple[int, int]]:
        """
        Extrahiert Spielerzahlen basierend auf dem SRV-Typ.

        MCP-Erkenntnisse zeigen verschiedene Offsets für verschiedene Typen.
        """
        if srv_pos == -1:
            return None

        # Verschiedene Offset-Patterns basierend auf Typ (MCP-korrigiert)
        if srv_type == 'null':
            # Für Null-Byte: Offsets +7 und +9
            offsets = [(7, 9)]
        elif srv_type == 'p':
            # Für Private Server: MCP-Analyse zeigt +10/+11 für aktive Spieler, +9/+11 fallback
            offsets = [
                # Beobachtung 172.29.100.29: plausibles Paar 1/6 bei SRV+29/SRV+50
                (29, 50),
                (10, 11), (9, 11), (7, 11),
                # zusätzliche pragmatische Kandidaten, beobachtet auf manchen 'p'-Servern
                (12, 14), (7, 9), (41, 45)
            ]  # Reihenfolge: etabliert, dann heuristisch
        else:
            # Für andere Typen: Teste mehrere Patterns
            offsets = [(7, 9), (9, 11), (7, 11), (41, 45), (12, 14), (15, 17)]

        # Teste die Offset-Patterns (MCP-korrigiert für aktuelle Spieler)
        for current_offset, max_offset in offsets:
            if srv_pos + max_offset < len(data):
                current_players = data[srv_pos + current_offset]
                max_players = data[srv_pos + max_offset]

                # Plausibilitätsprüfung
                if (0 <= current_players <= max_players <= 200 and
                    max_players > 0):
                    return current_players, max_players

        # Letzter Fallback nur für 'p'-Server: heuristische Suche in kleinem Fenster
        # Motiv: Es gibt Varianten, bei denen die Felder deutlich verschoben sind.
        if srv_type == 'p':
            window_start = max(0, srv_pos)
            window_end = min(len(data), srv_pos + 96)
            best_pair = None
            best_score = 1e9
            common_max_values = {6, 8, 10, 12, 14, 16, 20, 24, 32, 48, 64}
            for max_idx in range(srv_pos + 16, window_end):
                max_val = data[max_idx]
                if not (1 <= max_val <= 64):
                    continue
                # Suche current in der Nähe, bevorzugt vorher
                search_from = max(window_start, max_idx - 40)
                for cur_idx in range(search_from, max_idx):
                    cur_val = data[cur_idx]
                    if 0 <= cur_val <= max_val:
                        # Scoring: kleinere max-Werte bevorzugen (realistische Slot-Zahlen), Nähe der Felder
                        score = (0 if max_val in common_max_values else 10) + (max_idx - cur_idx)
                        if score < best_score:
                            best_score = score
                            best_pair = (cur_val, max_val)
            if best_pair is not None:
                return best_pair

        return None

    def _extract_game_mode(self, data: bytes) -> Optional[str]:
        """
        Extrahiert den Spielmodus aus dem Payload.

        Strategien (in dieser Reihenfolge):
        1) #SRV#-Offset-Erkennung: Für bestimmte Varianten (z. B. 'p') liegt die Mode-ID an einem festen Offset
        2) Marker-basierte Erkennung: Suche nach 0xFF 0xFF 0xFF 0xFF und nutze Byte an +7 als Modus-ID
        3) Stadium-Pattern-Fallback: Auswertung der Bytes nach dem 'Stadium' String
        4) Letzter Fallback: Keine Heuristik über Mapnamen (vermeidet Fehlzuordnung wie 'A01-Race')
        """
        # 1) Marker-basierte Erkennung
        mode_id = self._extract_game_mode_id_by_marker(data)
        if mode_id is not None:
            name = self._map_game_mode_id_to_name(mode_id)
            if name:
                return name

        # 2) Stadium-Pattern-Fallback
        mode_id = self._extract_game_mode_id_by_stadium_pattern(data)
        if mode_id is not None:
            name = self._map_game_mode_id_to_name(mode_id)
            if name:
                return name

        return None

    def _extract_game_mode_id_by_marker(self, data: bytes) -> Optional[int]:
        """
        Sucht nach dem 0xFFFFFFFF Marker und liest das Spielmodus-Byte bei +7.
        Laut Analyse liefert dieses Byte Werte wie 0x09 (Cup), 0x07 (Rounds), 0x06 (Team), 0x00 (Time Attack).
        """
        marker = b'\xff\xff\xff\xff'
        idx = data.find(marker)
        if idx != -1 and idx + 8 <= len(data):
            try:
                # Kandidaten-Offsets testen (+6, +7, +5), nur plausible IDs akzeptieren
                candidates = [idx + 7, idx + 6, idx + 5]
                valid_ids = {0, 1, 2, 3, 4, 5, 6, 7, 9}
                for off in candidates:
                    if 0 <= off < len(data):
                        val = data[off]
                        if val in valid_ids:
                            return val
            except Exception:
                return None
        return None

    def _extract_game_mode_id_by_stadium_pattern(self, data: bytes) -> Optional[int]:
        """
        Fallback-Erkennung über Byte-Muster relativ zum 'Stadium'-String.
        Bekanntes Mapping:
        - 0x01 0x20 => TimeAttack (ID 0)
        - 0x03 0x1e => Tournament (ID 3)
        - 0x06 0x32 => Team (ID 6)
        - 0x07 0x03 => Rounds (ID 7)
        - 0x09 xx   => Cup (ID 9)
        """
        # Suche 'Stadium' NACH dem '#SRV#'-Marker, um den richtigen Kontext zu erwischen
        anchor = b'Stadium'
        srv_pos = data.find(b'#SRV#')
        if srv_pos == -1:
            return None
        pos = data.find(anchor, srv_pos)
        if pos == -1:
            return None
        pattern_start = pos + len(anchor)
        # Wir benötigen mindestens ein kleines Fenster nach dem Anchor
        window_end = min(len(data), pattern_start + 32)
        if pattern_start >= window_end:
            return None

        # 1) Klassische Position b5/b6 (kompatibel zu früherer Implementierung)
        if len(data) > pattern_start + 6:
            b5 = data[pattern_start + 5]
            b6 = data[pattern_start + 6]
            if b5 == 0x01 and b6 == 0x20:
                return 0  # TimeAttack
            if b5 == 0x03 and b6 == 0x1e:
                return 3  # Tournament
            if b5 == 0x06 and b6 == 0x32:
                return 6  # Team
            if b5 == 0x07 and b6 == 0x03:
                return 7  # Rounds
            if b5 == 0x09:
                return 9  # Cup

        # 2) Flexibles Scannen im kleinen Fenster: suche bekannte Paare in beliebiger Ausrichtung
        window = data[pattern_start:window_end]
        # Paare, die als direkt aufeinanderfolgende Bytes auftreten sollten
        pair_to_mode = {
            (0x01, 0x20): 0,  # TimeAttack
            (0x03, 0x1e): 3,  # Tournament
            (0x06, 0x32): 6,  # Team
            (0x07, 0x03): 7,  # Rounds
        }
        for i in range(0, len(window) - 1):
            a, b = window[i], window[i + 1]
            if (a, b) in pair_to_mode:
                return pair_to_mode[(a, b)]
        # Cup kann als Einzelwert im Fenster auftreten
        if 0x09 in window:
            return 9

        # 3) Schwache Heuristik: Einzel-ID im Fenster (z. B. 0x07 für Rounds) bevorzugt, wenn eindeutig
        for candidate in (7, 6, 3, 0):
            if candidate in window:
                return candidate

        return None

    def _map_game_mode_id_to_name(self, mode_id: int) -> Optional[str]:
        """
        Mappt erkannte Modus-IDs auf sprechende Namen.
        Bevorzugt bekannte TMNF-Bezeichnungen.
        """
        mapping = {
            0: 'TimeAttack',
            3: 'Tournament',          # In manchen Quellen auch 'Tournament'; hier konservativ auf Laps mappen
            6: 'Team',
            7: 'Rounds',
            9: 'Cup',
        }
        # Weitere bekannte IDs aus Dokus (falls auftauchen)
        extra_aliases = {
            1: 'TimeAttack',
            2: 'Team',
            4: 'Stunts',
            5: 'Cup',
        }
        return mapping.get(mode_id) or extra_aliases.get(mode_id)

    def _extract_challenge_name(self, data: bytes, srv_pos: int, srv_type: str = None) -> Optional[str]:
        """
        Extrahiert den Challenge/Map-Namen basierend auf MCP-Analyse.

        WICHTIGE MCP-Erkenntnisse:
        - Default/Null Server: Challenge-Namen MIT 4-Byte Längenpräfix (Little Endian)
        - Private Server: Challenge-Namen OHNE Längenpräfix (direkte ASCII-Strings)

        Args:
            data: Die Rohdaten
            srv_pos: Position des #SRV# Markers
            srv_type: Typ des Servers ('null', 'p', etc.)

        Returns:
            Challenge-Name oder None
        """
        if srv_pos == -1:
            return None

        # Zuerst Prefix-Varianten versuchen (1/2/4 Bytes), unabhängig vom SRV-Typ
        name = self._extract_challenge_with_prefix(data, srv_pos)
        if name:
            return name
        # Fallback: direkte ASCII-Strings
        return self._extract_challenge_without_prefix(data, srv_pos)

    def _extract_challenge_with_prefix(self, data: bytes, srv_pos: int) -> Optional[str]:
        """
        Extrahiert Challenge-Namen mit Längenpräfix (1/2/4 Byte; LE für 2/4).
        """
        for prefix_size in (1, 2, 4):
            candidate = self._scan_challenge_with_prefix_size(data, srv_pos, prefix_size)
            if candidate:
                return candidate
        return None

    def _scan_challenge_with_prefix_size(self, data: bytes, srv_pos: int, prefix_size: int) -> Optional[str]:
        """
        Durchsucht den Bereich nach #SRV# nach einem length-prefixed String mit gegebener Präfixgröße.
        """
        search_start = srv_pos + 32
        search_end = min(len(data), srv_pos + 220)
        if search_start >= search_end:
            return None

        step = 1
        for offset in range(search_start, search_end - (prefix_size + 4), step):
            try:
                if offset + prefix_size >= len(data):
                    break

                if prefix_size == 1:
                    length = data[offset]
                elif prefix_size == 2:
                    length = struct.unpack('<H', data[offset:offset+2])[0]
                else:
                    length = struct.unpack('<I', data[offset:offset+4])[0]

                if not (5 <= length <= 40):
                    continue

                start = offset + prefix_size
                end = start + length
                if end > len(data):
                    continue

                segment = data[start:end]
                try:
                    raw_text = segment.decode('ascii', errors='ignore')
                except Exception:
                    continue

                # Nur druckbare Zeichen behalten
                cleaned = ''.join(ch for ch in raw_text if 32 <= ord(ch) <= 126)
                if not cleaned:
                    continue

                # Strikte Map-Erkennung als Substring
                strict = self._find_strict_challenge_in_text(cleaned)
                if strict:
                    return strict
            except Exception:
                continue
        return None

    def _extract_challenge_without_prefix(self, data: bytes, srv_pos: int) -> Optional[str]:
        """
        Extrahiert Challenge-Namen ohne Längenpräfix (für Private Server).
        """
        # Suche nach direkten ASCII-Strings ab SRV-Position
        search_start = srv_pos + 10
        search_data = data[search_start:]

        current_string = bytearray()
        found_strings = []

        for i, byte in enumerate(search_data):
            if 32 <= byte <= 126:  # Druckbare ASCII-Zeichen
                current_string.append(byte)
            else:
                if len(current_string) >= 5:  # Mindestens 5 Zeichen für Challenge-Namen
                    try:
                        string = current_string.decode('ascii')
                        if self._is_valid_challenge_name(string):
                            return string
                        found_strings.append(string)
                    except:
                        pass
                current_string = bytearray()

        # Letzten String nicht vergessen
        if len(current_string) >= 5:
            try:
                string = current_string.decode('ascii')
                if self._is_valid_challenge_name(string):
                    return string
                found_strings.append(string)
            except:
                pass

        # Fallback: Erste gültige Challenge aus gefundenen Strings
        for string in found_strings:
            if self._is_valid_challenge_name(string):
                return string

        return None

    def _is_valid_challenge_name(self, name: str) -> bool:
        """
        Prüft ob ein String ein gültiger Challenge/Map-Name ist.

        MCP-Erkenntnisse zeigen folgende Patterns:
        - Standard TrackMania Challenge-Namen: A01-Race, C02-Acrobatic, etc.
        - GBX-Referenzen
        - Race/Challenge Keywords

        Args:
            name: Zu prüfender String

        Returns:
            True wenn gültiger Challenge-Name
        """
        import re

        # Nur druckbare ASCII-Zeichen zulassen
        if any(ord(c) < 32 or ord(c) > 126 for c in name):
            return False

        # Zu kurz oder zu lang
        if len(name) < 3 or len(name) > 50:
            return False

        # Standard TrackMania Challenge Pattern: A01-Race, C02-Acrobatic
        # Aber nur vollständige bekannte Challenge-Namen (KEINE korrupten wie "C04-Raceh")
        standard_pattern = re.match(r'^[A-E]\d{2}-([A-Za-z]{4,})$', name)
        if standard_pattern:
            challenge_type = standard_pattern.group(1).lower()
            # Nur bekannte Challenge-Typen aus MCP-Analyse
            known_types = ['race', 'acrobatic', 'speed', 'endurance', 'platform', 'puzzle']
            # WICHTIG: "raceh" ist NICHT in known_types, also wird C04-Raceh abgelehnt!
            if challenge_type in known_types:
                return True

        # Verkürzte Namen: 5-Endurance, 1-Speed (nur bekannte Typen)
        short_pattern = re.match(r'^\d+-([A-Za-z]{4,})$', name)
        if short_pattern:
            challenge_type = short_pattern.group(1).lower()
            # Nur bekannte Challenge-Typen
            known_types = ['race', 'acrobatic', 'speed', 'endurance', 'platform', 'puzzle']
            if challenge_type in known_types:
                return True

        # Challenge/Race Keywords (aus MCP-Strings)
        challenge_keywords = [
            'race', 'speed', 'endurance', 'acrobatic', 'challenge',
            'track', 'circuit', 'course', 'stage'
        ]

        name_lower = name.lower()
        if any(keyword in name_lower for keyword in challenge_keywords):
            # Aber nicht wenn es offensichtlich ein Server-Name oder anderer String ist
            # Und mindestens ein Wort muss vollständig sein (nicht nur Teil eines Wortes)
            # WICHTIG: Blockiere korrupte Namen wie "raceh" (race + unbekanntes Ende)
            if (not any(exclude in name_lower for exclude in ['server', 'player', 'time', 'score']) and
                len(name) >= 4 and  # Mindestlänge
                not name_lower.endswith('p') and  # Nicht unvollständig wie "RaceP"
                not name_lower.endswith('h') and  # Nicht unvollständig wie "Raceh"
                not re.match(r'^[A-E]\d{2}-.*[ph]$', name, re.IGNORECASE) and  # Nicht Standard-Pattern mit 'p'/'h' am Ende
                (' ' in name or len(name) >= 5)):  # Entweder Leerzeichen oder mindestens 5 Zeichen
                return True

        # GBX-Pattern (aus MCP: .TrackMania.gbx)
        if '.gbx' in name_lower or 'trackmania' in name_lower:
            return True

        return False

    def _find_strict_challenge_in_text(self, text: str) -> Optional[str]:
        """
        Sucht in einem Text nach einem strikt passenden Challenge-Namen
        (z. B. A01-Race, C06-Speed, etc.) und gibt den ersten Treffer zurück.
        """
        import re
        pattern = re.compile(r'([A-E]\d{2}-(?:Race|Acrobatic|Speed|Endurance|Platform|Puzzle))', re.IGNORECASE)
        m = pattern.search(text)
        return m.group(0) if m else None

    def debug_payload(self, data: bytes) -> Dict[str, Any]:
        """
        Debug-Funktion zur Analyse eines Payloads.

        Args:
            data: Die Rohdaten

        Returns:
            Dictionary mit Debug-Informationen
        """
        debug_info = {
            'length': len(data),
            'hex_dump': data[:100].hex() if len(data) > 100 else data.hex(),
            'server_name_offset': 0x27,
            'srv_marker_pos': -1,
            'srv_type': None,
            'strings': [],
            'potential_player_offsets': {}
        }

        # Servername bei 0x27
        if len(data) >= 0x2b:
            server_name, bytes_read = self._deserialize_string(data, 0x27)
            debug_info['server_name'] = server_name
            debug_info['server_name_bytes_read'] = bytes_read

        # SRV Marker
        srv_pos = data.find(b'#SRV#')
        if srv_pos != -1:
            debug_info['srv_marker_pos'] = srv_pos
            if srv_pos + 5 < len(data):
                srv_type_byte = data[srv_pos + 5]
                debug_info['srv_type_byte'] = f'0x{srv_type_byte:02x}'
                if srv_type_byte == 0x00:
                    debug_info['srv_type'] = 'null'
                elif chr(srv_type_byte) in ['f', 's', 'p']:
                    debug_info['srv_type'] = chr(srv_type_byte)

        # Alle Strings
        debug_info['strings'] = self._extract_all_strings(data)

        # MCP-basierte Challenge-Namen Extraktion
        challenge_name = self._extract_challenge_name(data, srv_pos)
        debug_info['mcp_challenge_name'] = challenge_name
        debug_info['challenge_extraction_method'] = 'MCP-based' if challenge_name else 'fallback'

        # Potentielle Spielerzahl-Offsets
        if srv_pos != -1:
            test_offsets = [(7, 9), (41, 45), (12, 14), (15, 17)]
            for curr_off, max_off in test_offsets:
                if srv_pos + max_off < len(data):
                    curr = data[srv_pos + curr_off]
                    max_val = data[srv_pos + max_off]
                    debug_info['potential_player_offsets'][f'+{curr_off}/+{max_off}'] = f'{curr}/{max_val}'

        return debug_info
