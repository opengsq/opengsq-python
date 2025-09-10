import asyncio
import socket
from opengsq.protocol_base import ProtocolBase
from opengsq.responses.directplay.status import Status
from opengsq.binary_reader import BinaryReader


class DirectPlay(ProtocolBase):
    """
    DirectPlay Protocol Base Class
    
    DirectPlay ist ein Netzwerkprotokoll, das von verschiedenen Spielen verwendet wird,
    insbesondere von älteren Microsoft-Spielen wie Age of Empires 1 und 2.
    
    Das Protokoll funktioniert folgendermaßen:
    1. Ein lokaler TCP Socket wird auf Port 2300 geöffnet
    2. Eine UDP-Anfrage wird an Port 47624 des Spieleservers gesendet
    3. Der Spieleserver antwortet über TCP an unseren lokalen Port 2300
    
    DirectPlay UDP-Payload Struktur (52 Bytes):
    - Bytes 0-3:   Header (34 00 b0 fa)
    - Bytes 4-7:   Protokoll Info (02 00 08 fc)
    - Bytes 8-19:  Padding/Reserved (alle 00)
    - Bytes 20-23: "play" - DirectPlay Identifikation
    - Bytes 24-27: Weitere Header-Info (02 00 0e 00)
    - Bytes 28-43: Spiel-spezifische GUID (16 Bytes, unterscheidet Spiele)
    - Bytes 44-47: Padding/Reserved (00 00 00 00)
    - Bytes 48-51: Version/Type ID (unterscheidet Spielversionen)
    """
    
    full_name = "DirectPlay Protocol"
    
    # DirectPlay Konstanten
    DIRECTPLAY_UDP_PORT = 47624
    DIRECTPLAY_TCP_PORT = 2300
    
    def __init__(self, host: str, port: int = DIRECTPLAY_UDP_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self._tcp_listen_port = self.DIRECTPLAY_TCP_PORT
        
    async def get_status(self) -> Status:
        """
        Führt eine DirectPlay-Abfrage durch.
        
        Returns:
            Status: Parsed server status information
        """
        # Erstelle den UDP Query Packet (wird von Subklassen überschrieben)
        query_packet = self._build_query_packet()
        
        # Führe die DirectPlay-Kommunikation durch
        response_data = await self._directplay_communicate(query_packet)
        
        # Parse die Antwort (wird von Subklassen überschrieben)
        parsed_data = self._parse_response(response_data)
        
        return Status(**parsed_data)
    
    async def _directplay_communicate(self, query_packet: bytes) -> bytes:
        """
        Führt die DirectPlay-spezifische Kommunikation durch:
        1. Öffnet einen TCP Socket auf einem verfügbaren Port zum Empfangen der Antwort
        2. Sendet UDP Query an den Spieleserver
        3. Wartet auf TCP-Antwort
        
        Args:
            query_packet: Das UDP-Paket, das an den Server gesendet wird
            
        Returns:
            bytes: Die TCP-Antwort vom Server
        """
        # Verwende asyncio.Future für saubere async communication
        response_future = asyncio.Future()
        actual_tcp_port = self._tcp_listen_port
        
        class DirectPlayTcpProtocol(asyncio.Protocol):
            def __init__(self):
                self.transport = None
                self.received_data = b''
                
            def connection_made(self, transport):
                self.transport = transport
                
            def data_received(self, data):
                self.received_data += data
                # Setze das Future-Result mit den empfangenen Daten
                if not response_future.done():
                    response_future.set_result(self.received_data)
                # Schließe die Verbindung nach dem Empfang der Daten  
                if self.transport:
                    self.transport.close()
                
            def connection_lost(self, exc):
                if exc and not response_future.done():
                    response_future.set_exception(Exception(f"Connection lost: {exc}"))
        
        try:
            # TCP Server starten - versuche verschiedene Ports falls 2300 belegt ist
            loop = asyncio.get_running_loop()
            server = None
            for port_offset in range(10):  # Versuche Ports 2300-2309
                try:
                    actual_tcp_port = self._tcp_listen_port + port_offset
                    server = await loop.create_server(
                        DirectPlayTcpProtocol,
                        '0.0.0.0',
                        actual_tcp_port
                    )
                    break
                except OSError:
                    if port_offset == 9:  # Letzter Versuch
                        raise Exception(f"Could not bind TCP server to ports {self._tcp_listen_port}-{actual_tcp_port}")
                    continue
            
            # Sicherstellen, dass der Server wirklich läuft
            await server.start_serving()
            await asyncio.sleep(0.1)  # Kurz warten bis Server bereit ist
            
            # UDP Query senden
            await self._send_udp_query(query_packet)
            
            # Warten auf TCP-Antwort mit asyncio.Future
            response_data = await asyncio.wait_for(response_future, timeout=self._timeout)
            
            return response_data
            
        except asyncio.TimeoutError:
            raise Exception(f"DirectPlay Timeout nach {self._timeout} Sekunden")
        finally:
            if server:
                server.close()
                await server.wait_closed()
    
    async def _send_udp_query(self, query_packet: bytes):
        """
        Sendet den UDP Query an den Spieleserver.
        
        Args:
            query_packet: Das UDP-Paket, das gesendet wird
        """
        loop = asyncio.get_running_loop()
        
        # UDP Socket erstellen
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            local_addr=('0.0.0.0', 0)
        )
        
        try:
            # Query senden
            transport.sendto(query_packet, (self._host, self._port))
            # Kurz warten um sicherzustellen, dass das Paket gesendet wurde
            await asyncio.sleep(0.05)
        finally:
            transport.close()
    
    def _build_query_packet(self) -> bytes:
        """
        Erstellt das UDP Query Packet.
        Muss von Subklassen implementiert werden.
        
        Returns:
            bytes: Das Query Packet
        """
        raise NotImplementedError("Subclasses must implement _build_query_packet")
    
    def _parse_response(self, buffer: bytes) -> dict:
        """
        Parsed die TCP-Antwort vom Server.
        Muss von Subklassen implementiert werden.
        
        Args:
            buffer: Die rohen Antwortdaten
            
        Returns:
            dict: Geparste Server-Informationen
        """
        raise NotImplementedError("Subclasses must implement _parse_response")
    
    def _read_string(self, br: BinaryReader, encoding: str = 'utf-8') -> str:
        """
        Hilfsfunktion zum Lesen von Strings aus BinaryReader.
        
        Args:
            br: BinaryReader instance
            encoding: String encoding (default: utf-8)
            
        Returns:
            str: Der gelesene String
        """
        # Standard DirectPlay String Format (kann überschrieben werden)
        length = br.read_uint16()
        if length == 0:
            return ""
        return br.read_bytes(length).decode(encoding, errors='ignore')
