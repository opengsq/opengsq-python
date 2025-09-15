from opengsq.protocols.directplay import DirectPlay
from opengsq.responses.aoe2.status import Status
from opengsq.binary_reader import BinaryReader


class AoE2(DirectPlay):
    """
    Age of Empires 2 DirectPlay Protocol
    
    Erweitert das DirectPlay Basis-Protokoll um spezifische 
    Age of Empires 2 Implementierungsdetails.
    """
    
    full_name = "Age of Empires 2 DirectPlay Protocol"
    
    # AoE2 spezifische Konstanten und Payload
    AOE2_UDP_PAYLOAD = bytes.fromhex("3400b0fa020008fc000000000000000000000000706c617902000e0060a269fb3150d311a2d4006097ba65500000000011000000")
    
    # DirectPlay Payload-Struktur für AoE2:
    # Bytes 0-27:  Gemeinsamer DirectPlay Header (identisch mit AoE1)
    # Bytes 20-23: "play" - DirectPlay Identifikation
    # Bytes 28-43: Spiel-spezifische GUID: 60a269fb-3150-d311-a2d4-006097ba6550
    # Bytes 44-47: Padding/Reserved (00 00 00 00)  
    # Bytes 48-51: Version/Type ID: 11 00 00 00 (unterscheidet sich von AoE1)
    AOE2_GAME_GUID = "60a269fb-3150-d311-a2d4-006097ba6550"
    
    # AoE2 Civilizations
    CIVILIZATIONS = {
        0: "Unknown",
        1: "Britons",
        2: "Franks", 
        3: "Goths",
        4: "Teutons",
        5: "Japanese",
        6: "Chinese",
        7: "Byzantines",
        8: "Persians",
        9: "Saracens",
        10: "Turks",
        11: "Vikings",
        12: "Mongols",
        13: "Celts",
        14: "Spanish",
        15: "Aztecs",
        16: "Mayans",
        17: "Huns",
        18: "Koreans"
    }
    
    # AoE2 Game Modes
    GAME_MODES = {
        0: "Random Map",
        1: "Regicide",
        2: "Death Match",
        3: "Scenario",
        4: "Campaign",
        5: "King of the Hill",
        6: "Wonder Race",
        7: "Defend the Wonder"
    }
    
    def __init__(self, host: str, port: int = DirectPlay.DIRECTPLAY_UDP_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        
    def _build_query_packet(self) -> bytes:
        """
        Erstellt das AoE2-spezifische UDP Query Packet.
        
        Verwendet den echten DirectPlay-Payload für Age of Empires 2:
        3400b0fa020008fc000000000000000000000000706c617902000e0060a269fb3150d311a2d4006097ba65500000000011000000
        
        Returns:
            bytes: Das AoE2 Query Packet
        """
        return self.AOE2_UDP_PAYLOAD
    
    def _parse_response(self, buffer: bytes) -> dict:
        """
        Parsed die TCP-Antwort vom AoE2 Server.
        
        Erweitert die Basis-DirectPlay-Parsing um AoE2-spezifische Logik.
        
        Args:
            buffer: Die rohen TCP-Antwortdaten
            
        Returns:
            dict: Geparste AoE2 Server-Informationen
        """
        # Nutze die Basis-DirectPlay-Parsing-Logik
        result = super()._parse_response(buffer)
        
        # AoE2-spezifische Anpassungen
        result['game_type'] = 'Age of Empires II'
        
        # Extrahiere echte Version-Informationen
        version_info = self._extract_version_info(buffer)
        if 'likely_version' in version_info:
            result['game_version'] = version_info['likely_version'].replace('Age of Empires II ', '')
        elif 'detected_version' in version_info:
            result['game_version'] = version_info['detected_version'].replace('Age of Empires II ', '')
        elif 'game_version' in version_info:
            result['game_version'] = version_info['game_version'].replace('Age of Empires II ', '')
        else:
            result['game_version'] = '2.0a'  # Fallback
        
        # Versuche AoE2-spezifische Daten zu parsen
        try:
            aoe2_data = self._parse_aoe2_specific_data(buffer)
            result.update(aoe2_data)
        except Exception as e:
            result['raw']['aoe2_parse_error'] = str(e)
        
        # Debug-Informationen hinzufügen
        result['raw']['game_guid'] = self.AOE2_GAME_GUID
        result['raw']['buffer_size'] = len(buffer)
        result['raw']['buffer_preview'] = buffer[:50].hex() if len(buffer) > 50 else buffer.hex()
        result['raw']['version_info'] = version_info
        result['raw']['civilizations'] = self.CIVILIZATIONS
        result['raw']['game_modes'] = self.GAME_MODES
        
        return result
    
    def _parse_aoe2_specific_data(self, buffer: bytes) -> dict:
        """
        Parsed AoE2-spezifische Daten aus der DirectPlay-Antwort.
        
        Args:
            buffer: Die rohen Antwortdaten
            
        Returns:
            dict: AoE2-spezifische Daten
        """
        result = {}
        
        if len(buffer) < 10:
            return result
        
        br = BinaryReader(buffer)
        
        try:
            # Skip DirectPlay Header (4 bytes)
            br.read_bytes(4)
            
            # Versuche, AoE2-spezifische Strukturen zu erkennen
            remaining_data = br.read_bytes(br.remaining_bytes())
            
            # Suche nach Spielnamen (AoE2 verwendet ASCII-Strings)
            game_name = self._extract_aoe2_game_name(remaining_data)
            if game_name:
                result['name'] = game_name
            
            # Versuche Spieleranzahl zu ermitteln (ähnlich wie AoE1)
            player_count = self._extract_aoe2_player_count(remaining_data)
            if player_count >= 0:
                result['num_players'] = player_count
                
            # Versuche Max Players zu ermitteln
            max_players = self._extract_aoe2_max_players(remaining_data)
            if max_players > 0:
                result['max_players'] = max_players
            
            # Versuche Kartennamen zu extrahieren
            map_name = self._extract_aoe2_map_name(remaining_data)
            if map_name:
                result['map'] = map_name
            
            # AoE2-spezifische Spielmodi
            game_mode = self._extract_aoe2_game_mode(remaining_data)
            if game_mode:
                result['game_mode'] = game_mode
                
        except Exception as e:
            result['aoe2_specific_error'] = str(e)
        
        return result
    
    def _extract_aoe2_game_name(self, data: bytes) -> str:
        """
        Versucht, den Spielnamen aus den AoE2-Daten zu extrahieren.
        
        AoE2 verwendet ASCII-Strings mit 32-bit Length-Prefix.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            str: Der Spielname oder leer
        """
        try:
            # AoE2 String-Format: 32-bit length prefix + ASCII string + null terminator
            search_start = max(0, len(data) - 100)
            
            for i in range(search_start, len(data) - 8, 4):
                if i + 4 < len(data):
                    # Lese 32-bit Längenwert (little-endian)
                    potential_length = int.from_bytes(data[i:i+4], 'little')
                    
                    # Plausible Länge für einen Spielnamen (3-200 chars für ASCII, kann auch komplette String-Sektion sein)
                    if 3 <= potential_length <= 200:
                        name_start = i + 4
                        
                        # Begrenze auf verfügbare Daten
                        available_length = len(data) - name_start
                        effective_length = min(potential_length, available_length)
                        
                        if effective_length > 0:
                            name_bytes = data[name_start:name_start + effective_length]
                            
                            try:
                                # AoE2 verwendet ASCII/UTF-8 encoding
                                decoded = name_bytes.decode('ascii', errors='strict')
                                
                                # Finde den ersten null-terminierten String
                                null_pos = decoded.find('\x00')
                                if null_pos >= 0:
                                    clean_name = decoded[:null_pos].strip()
                                else:
                                    clean_name = decoded.strip()
                                
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
    
    def _extract_aoe2_player_count(self, data: bytes) -> int:
        """
        Versucht, die Spieleranzahl aus den AoE2-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            int: Die Spieleranzahl oder 0
        """
        try:
            # Verwende ähnliche Logik wie bei AoE1
            if len(data) >= 48:
                session_start = 40
                
                if len(data) >= session_start + 28:
                    max_players_offset = session_start + 24
                    current_players_offset = session_start + 28
                    
                    max_players = int.from_bytes(data[max_players_offset:max_players_offset+4], 'little')
                    current_players = int.from_bytes(data[current_players_offset:current_players_offset+4], 'little')
                    
                    # Validierung der Werte (AoE2 unterstützt bis zu 8 Spieler)
                    if 1 <= max_players <= 8 and 0 <= current_players <= max_players:
                        return current_players
                        
            # Fallback: Suche nach plausiblen Werten
            for i in range(len(data) - 8):
                value = int.from_bytes(data[i:i+4], 'little')
                next_value = int.from_bytes(data[i+4:i+8], 'little')
                
                if (0 <= value <= 8 and 1 <= next_value <= 8 and value <= next_value):
                    return value
                    
        except Exception:
            pass
        
        return 0
    
    def _extract_aoe2_max_players(self, data: bytes) -> int:
        """
        Versucht, die maximale Spieleranzahl aus den AoE2-Daten zu extrahieren.
        
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
                    max_players_offset = session_start + 24
                    current_players_offset = session_start + 28
                    
                    max_players = int.from_bytes(data[max_players_offset:max_players_offset+4], 'little')
                    current_players = int.from_bytes(data[current_players_offset:current_players_offset+4], 'little')
                    
                    if 1 <= max_players <= 8 and 0 <= current_players <= max_players:
                        return max_players
                        
            # Fallback: Suche nach dem zweiten Wert im Spieler-Paar
            for i in range(len(data) - 8):
                value = int.from_bytes(data[i:i+4], 'little')
                next_value = int.from_bytes(data[i+4:i+8], 'little')
                
                if (0 <= value <= 8 and 1 <= next_value <= 8 and value <= next_value):
                    return next_value
                    
        except Exception:
            pass
        
        return 8  # Standard für AoE2
    
    def _extract_aoe2_map_name(self, data: bytes) -> str:
        """
        Versucht, den Kartennamen aus den AoE2-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            str: Der Kartenname oder leer
        """
        # Bekannte AoE2-Kartennamen
        known_maps = [
            "Arabia", "Black Forest", "Baltic", "Mediterranean", "Rivers", 
            "Coastal", "Continental", "Highland", "Islands", "Team Islands",
            "Random Map", "Archipelago", "Arena", "Fortress", "Gold Rush",
            "Nomad", "Oasis", "Random Land Map", "Scandinavia"
        ]
        
        try:
            # Suche nach bekannten Kartennamen in den ASCII-Daten
            data_str = data.decode('ascii', errors='ignore').lower()
            
            for map_name in known_maps:
                if map_name.lower() in data_str:
                    return map_name
                    
        except Exception:
            pass
        
        return "Unknown Map"
    
    def _extract_aoe2_game_mode(self, data: bytes) -> str:
        """
        Versucht, den Spielmodus aus den AoE2-Daten zu extrahieren.
        
        Args:
            data: Die Daten nach dem DirectPlay-Header
            
        Returns:
            str: Der Spielmodus oder leer
        """
        try:
            data_str = data.decode('ascii', errors='ignore').lower()
            
            for mode_id, mode_name in self.GAME_MODES.items():
                if mode_name.lower() in data_str:
                    return mode_name
                    
        except Exception:
            pass
        
        return "Random Map"  # Standard-Modus
    
    def _get_civilization_name(self, civ_id: int) -> str:
        """
        Konvertiert eine Zivilisations-ID zu einem lesbaren Namen.
        
        Args:
            civ_id: Die Zivilisations-ID
            
        Returns:
            str: Der Zivilisationsname
        """
        return self.CIVILIZATIONS.get(civ_id, f"Unknown ({civ_id})")
    
    def _get_game_mode_name(self, mode_id: int) -> str:
        """
        Konvertiert eine Game Mode ID zu einem lesbaren Namen.
        
        Args:
            mode_id: Die Game Mode ID
            
        Returns:
            str: Der Game Mode Name
        """
        return self.GAME_MODES.get(mode_id, f"Unknown ({mode_id})")
