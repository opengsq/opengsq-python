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
        
        TODO: Dies ist ein Platzhalter. Die echte Parsing-Logik muss 
        durch Analyse der TCP-Pakete implementiert werden.
        
        Args:
            buffer: Die rohen TCP-Antwortdaten
            
        Returns:
            dict: Geparste AoE2 Server-Informationen
        """
        if len(buffer) < 4:
            raise Exception("Antwort zu kurz für AoE2 DirectPlay Protokoll")
            
        br = BinaryReader(buffer)
        
        # Placeholder Parsing Logic
        # TODO: Echte AoE2 Paket-Struktur implementieren
        
        # Beispiel DirectPlay Header lesen
        magic = br.read_bytes(4)
        
        # Placeholder Werte
        result = {
            'name': 'AoE2 Server (Placeholder)',
            'game_type': 'Age of Empires II',
            'map': 'Unknown Map',
            'num_players': 0,
            'max_players': 8,
            'password_protected': False,
            'game_version': '2.0',
            'game_mode': 'Random Map',
            'difficulty': 'Standard',
            'speed': 'Normal',
            'players': [],
            'raw': {
                'magic': magic.hex(),
                'buffer_length': len(buffer),
                'full_buffer': buffer.hex(),
                'civilizations': self.CIVILIZATIONS,
                'game_modes': self.GAME_MODES
            }
        }
        
        return result
    
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
