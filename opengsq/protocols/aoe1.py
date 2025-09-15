from opengsq.protocols.directplay import DirectPlay
from opengsq.responses.aoe1.status import Status
from opengsq.binary_reader import BinaryReader


class AoE1(DirectPlay):
    """
    Age of Empires 1 DirectPlay Protocol
    
    Erweitert das DirectPlay Basis-Protokoll um spezifische 
    Age of Empires 1 Implementierungsdetails.
    """
    
    full_name = "Age of Empires 1 DirectPlay Protocol"
    
    # AoE1 spezifische Konstanten und Payload
    AOE1_UDP_PAYLOAD = bytes.fromhex("3400b0fa020008fc000000000000000000000000706c617902000e0082e92234891ad111b09300a024c747760000000001000000")
    
    # DirectPlay Payload-Struktur für AoE1:
    # Bytes 0-27:  Gemeinsamer DirectPlay Header (identisch mit AoE2)
    # Bytes 20-23: "play" - DirectPlay Identifikation
    # Bytes 28-43: Spiel-spezifische GUID: 82e92234-891a-d111-b093-00a024c74776
    # Bytes 44-47: Padding/Reserved (00 00 00 00)
    # Bytes 48-51: Version/Type ID: 01 00 00 00 (unterscheidet sich von AoE2)
    AOE1_GAME_GUID = "82e92234-891a-d111-b093-00a024c74776"
    
    def __init__(self, host: str, port: int = DirectPlay.DIRECTPLAY_UDP_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        
    def _build_query_packet(self) -> bytes:
        """
        Erstellt das AoE1-spezifische UDP Query Packet.
        
        Verwendet den echten DirectPlay-Payload für Age of Empires 1:
        3400b0fa020008fc000000000000000000000000706c617902000e0082e92234891ad111b09300a024c747760000000001000000
        
        Returns:
            bytes: Das AoE1 Query Packet
        """
        return self.AOE1_UDP_PAYLOAD
    
    def _parse_response(self, buffer: bytes) -> dict:
        """
        Parsed die TCP-Antwort vom AoE1 Server.
        
        Erweitert die Basis-DirectPlay-Parsing um AoE1-spezifische Logik.
        
        Args:
            buffer: Die rohen TCP-Antwortdaten
            
        Returns:
            dict: Geparste AoE1 Server-Informationen
        """
        # Nutze die Basis-DirectPlay-Parsing-Logik
        result = super()._parse_response(buffer)
        
        # AoE1-spezifische Anpassungen
        result['game_type'] = 'Age of Empires'
        
        # Extrahiere echte Version-Informationen
        version_info = self._extract_version_info(buffer)
        if 'likely_version' in version_info:
            result['game_version'] = version_info['likely_version'].replace('Age of Empires ', '')
        elif 'detected_version' in version_info:
            result['game_version'] = version_info['detected_version'].replace('Age of Empires ', '')
        elif 'game_version' in version_info:
            result['game_version'] = version_info['game_version'].replace('Age of Empires ', '')
        else:
            result['game_version'] = '1.0c'  # Fallback
        
        # Versuche AoE1-spezifische Daten zu parsen
        try:
            aoe1_data = self._parse_aoe1_specific_data(buffer)
            result.update(aoe1_data)
        except Exception as e:
            result['raw']['aoe1_parse_error'] = str(e)
        
        # Debug-Informationen hinzufügen
        result['raw']['game_guid'] = self.AOE1_GAME_GUID
        result['raw']['buffer_size'] = len(buffer)
        result['raw']['buffer_preview'] = buffer[:50].hex() if len(buffer) > 50 else buffer.hex()
        result['raw']['version_info'] = version_info
        
        return result
    
    def _parse_aoe1_specific_data(self, buffer: bytes) -> dict:
        """
        Parsed AoE1-spezifische Daten aus der DirectPlay-Antwort.
        
        Args:
            buffer: Die rohen Antwortdaten
            
        Returns:
            dict: AoE1-spezifische Daten
        """
        result = {}
        
        if len(buffer) < 10:
            return result
        
        br = BinaryReader(buffer)
        
        try:
            # Skip DirectPlay Header (4 bytes)
            br.read_bytes(4)
            
            # Versuche, AoE1-spezifische Strukturen zu erkennen
            # AoE1 verwendet oft spezifische Byte-Sequenzen
            
            # Suche nach bekannten AoE1-Mustern
            remaining_data = br.read_bytes(br.remaining_bytes())
            
            # Suche nach Spielnamen (oft nach bestimmten Byte-Sequenzen)
            game_name = self._extract_aoe1_game_name(remaining_data)
            if game_name:
                result['name'] = game_name
            
            # Versuche Spieleranzahl zu ermitteln
            player_count = self._extract_aoe1_player_count(remaining_data)
            if player_count >= 0:  # 0 ist auch gültig (leerer Server)
                result['num_players'] = player_count
                
            # Versuche Max Players zu ermitteln
            max_players = self._extract_aoe1_max_players(remaining_data)
            if max_players > 0:
                result['max_players'] = max_players
            
            # Versuche Kartennamen zu extrahieren
            map_name = self._extract_aoe1_map_name(remaining_data)
            if map_name:
                result['map'] = map_name
            
            # AoE1-spezifische Spielmodi
            game_mode = self._extract_aoe1_game_mode(remaining_data)
            if game_mode:
                result['game_mode'] = game_mode
                
        except Exception as e:
            result['aoe1_specific_error'] = str(e)
        
        return result
    
    def _extract_aoe1_game_name(self, data: bytes) -> str:
        """
        Versucht, den Spielnamen aus den AoE1-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            str: Der Spielname oder leer
        """
        try:
            # Der Spielname ist typischerweise am Ende des DirectPlay-Pakets
            # als length-prefixed UTF-16LE String
            
            # Suche nach length-prefixed Unicode-Strings
            # Typischerweise bei den letzten ~50 Bytes des Pakets
            search_start = max(0, len(data) - 100)
            
            # Suche nach 16-bit Length-Prefix für UTF-16LE String
            for i in range(search_start, len(data) - 8, 2):
                if i + 2 < len(data):
                    # Lese 16-bit Längenwert (little-endian)
                    potential_length = int.from_bytes(data[i:i+2], 'little')
                    
                    # Plausible Länge für einen Spielnamen (6-200 chars = 12-400 bytes für UTF-16LE)
                    if 12 <= potential_length <= 400 and potential_length % 2 == 0:
                        # Der String kann Padding haben - prüfe beide Varianten
                        for padding in [0, 2]:  # Mit und ohne 2-Byte Padding
                            name_start = i + 2 + padding
                            
                            # Begrenze die Länge auf das verfügbare Data
                            available_length = len(data) - name_start
                            effective_length = min(potential_length - padding, available_length)
                            
                            if effective_length > 0 and name_start < len(data):
                                name_bytes = data[name_start:name_start + effective_length]
                                
                                try:
                                    decoded = name_bytes.decode('utf-16le', errors='strict')
                                    clean_name = decoded.rstrip('\x00').strip()
                                    
                                    # Validierung: Name sollte druckbare Zeichen enthalten
                                    if (len(clean_name) >= 3 and 
                                        all(ord(c) >= 32 or c.isspace() for c in clean_name) and
                                        any(c.isalnum() for c in clean_name)):
                                        return clean_name
                                except UnicodeDecodeError:
                                    continue
                            
        except Exception:
            pass
        
        return ""
    
    def _extract_aoe1_player_count(self, data: bytes) -> int:
        """
        Versucht, die Spieleranzahl aus den AoE1-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            int: Die Spieleranzahl oder 0
        """
        try:
            # DirectPlay Session Data beginnt nach dem GUID (ab Offset 40 vom Header)
            # Die Spielerzahl steht typischerweise bei festen Offsets
            
            # Bei AoE1 sind die Session-Daten strukturiert:
            # Offset 64-67: Max Players (8)
            # Offset 68-71: Current Players (1)
            
            if len(data) >= 48:  # Genug Daten für Session Info
                # Offset 40 (nach 4-byte header) entspricht Offset 68 in absoluten Koordinaten  
                session_start = 40  # Nach dem Header
                
                # Max players bei Offset +24 im Session-Bereich
                if len(data) >= session_start + 28:
                    max_players_offset = session_start + 24  # Offset 64 absolut
                    current_players_offset = session_start + 28  # Offset 68 absolut
                    
                    max_players = int.from_bytes(data[max_players_offset:max_players_offset+4], 'little')
                    current_players = int.from_bytes(data[current_players_offset:current_players_offset+4], 'little')
                    
                    # Validierung der Werte
                    if 1 <= max_players <= 8 and 0 <= current_players <= max_players:
                        return current_players
                    
            # Fallback: Suche nach plausiblen Werten
            for i in range(len(data) - 8):
                value = int.from_bytes(data[i:i+4], 'little')
                next_value = int.from_bytes(data[i+4:i+8], 'little')
                
                # Suche nach dem Muster: current_players, max_players
                if (0 <= value <= 8 and 1 <= next_value <= 8 and value <= next_value):
                    return value
                    
        except Exception:
            pass
        
        return 0
    
    def _extract_aoe1_max_players(self, data: bytes) -> int:
        """
        Versucht, die maximale Spieleranzahl aus den AoE1-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            int: Die maximale Spieleranzahl oder 0
        """
        try:
            # Verwende dieselbe Logik wie bei player_count, aber für max_players
            if len(data) >= 48:
                session_start = 40
                
                if len(data) >= session_start + 28:
                    max_players_offset = session_start + 24  # Offset 64 absolut
                    current_players_offset = session_start + 28  # Offset 68 absolut
                    
                    max_players = int.from_bytes(data[max_players_offset:max_players_offset+4], 'little')
                    current_players = int.from_bytes(data[current_players_offset:current_players_offset+4], 'little')
                    
                    # Validierung der Werte
                    if 1 <= max_players <= 8 and 0 <= current_players <= max_players:
                        return max_players
                        
            # Fallback: Suche nach dem zweiten Wert im Spieler-Paar
            for i in range(len(data) - 8):
                value = int.from_bytes(data[i:i+4], 'little')
                next_value = int.from_bytes(data[i+4:i+8], 'little')
                
                # Suche nach dem Muster: current_players, max_players
                if (0 <= value <= 8 and 1 <= next_value <= 8 and value <= next_value):
                    return next_value
                    
        except Exception:
            pass
        
        return 8  # Standard für AoE1
    
    def _extract_aoe1_map_name(self, data: bytes) -> str:
        """
        Versucht, den Kartennamen aus den AoE1-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            str: Der Kartenname oder leer
        """
        # Bekannte AoE1-Kartennamen
        known_maps = [
            "River Nile", "Continental", "Coastal", "Inland", "Highland", 
            "Mediterranean", "Hill Country", "Large Islands", "Small Islands",
            "King of the Hill", "Unknown", "Random Map"
        ]
        
        try:
            # Suche nach bekannten Kartennamen in den Daten
            data_str = data.decode('ascii', errors='ignore').lower()
            
            for map_name in known_maps:
                if map_name.lower() in data_str:
                    return map_name
                    
        except Exception:
            pass
        
        return "Unknown Map"
    
    def _extract_aoe1_game_mode(self, data: bytes) -> str:
        """
        Versucht, den Spielmodus aus den AoE1-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            str: Der Spielmodus oder leer
        """
        # AoE1 Spielmodi
        game_modes = ["Random Map", "Death Match", "Scenario"]
        
        try:
            data_str = data.decode('ascii', errors='ignore').lower()
            
            for mode in game_modes:
                if mode.lower() in data_str:
                    return mode
                    
        except Exception:
            pass
        
        return "Random Map"  # Standard-Modus
