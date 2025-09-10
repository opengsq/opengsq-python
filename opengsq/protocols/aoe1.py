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
        
        TODO: Dies ist ein Platzhalter. Die echte Parsing-Logik muss 
        durch Analyse der TCP-Pakete implementiert werden.
        
        Args:
            buffer: Die rohen TCP-Antwortdaten
            
        Returns:
            dict: Geparste AoE1 Server-Informationen
        """
        if len(buffer) < 4:
            raise Exception("Antwort zu kurz für AoE1 DirectPlay Protokoll")
            
        br = BinaryReader(buffer)
        
        # Placeholder Parsing Logic
        # TODO: Echte AoE1 Paket-Struktur implementieren
        
        # Beispiel DirectPlay Header lesen
        magic = br.read_bytes(4)
        
        # Placeholder Werte
        result = {
            'name': 'AoE1 Server (Placeholder)',
            'game_type': 'Age of Empires',
            'map': 'Unknown Map',
            'num_players': 0,
            'max_players': 8,
            'password_protected': False,
            'game_version': '1.0',
            'game_mode': 'Standard',
            'difficulty': 'Standard',
            'speed': 'Normal',
            'players': [],
            'raw': {
                'magic': magic.hex(),
                'buffer_length': len(buffer),
                'full_buffer': buffer.hex()
            }
        }
        
        return result
