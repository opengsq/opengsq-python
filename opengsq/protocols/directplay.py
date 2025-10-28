import asyncio
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

        # Filtere nur gültige Status-Parameter
        status_fields = {
            'name', 'game_type', 'map', 'num_players', 'max_players',
            'password_protected', 'game_version', 'game_mode',
            'difficulty', 'speed', 'players', 'raw'
        }

        filtered_data = {k: v for k, v in parsed_data.items() if k in status_fields}

        return Status(**filtered_data)

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
        Kann von Subklassen überschrieben werden für spezifische Implementierungen.

        Args:
            buffer: Die rohen Antwortdaten

        Returns:
            dict: Geparste Server-Informationen
        """
        if len(buffer) < 4:
            raise Exception("DirectPlay Antwort zu kurz")

        br = BinaryReader(buffer)

        # DirectPlay Header lesen
        magic = br.read_bytes(4)

        # Basis-Parsing für DirectPlay-Pakete
        result = {
            'name': 'DirectPlay Server',
            'game_type': 'DirectPlay Game',
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

        # Versuche weitere Daten zu parsen, falls vorhanden
        try:
            result.update(self._parse_directplay_data(br))
        except Exception as e:
            # Fallback bei Parsing-Fehlern
            result['raw']['parse_error'] = str(e)

        return result

    def _parse_directplay_data(self, br: BinaryReader) -> dict:
        """
        Parsed erweiterte DirectPlay-Daten basierend auf Wireshark-Implementierung.

        Args:
            br: BinaryReader instance mit verbleibendem Buffer

        Returns:
            dict: Geparste DirectPlay-Daten
        """
        result = {}

        try:
            # DirectPlay-Protokoll basiert auf Sessions und Messages
            # Versuche, bekannte DirectPlay-Strukturen zu erkennen

            if br.remaining_bytes() >= 8:
                # Session ID (32-bit)
                session_id = br.read_uint32()
                result['session_id'] = session_id

                # Message Type (32-bit)
                message_type = br.read_uint32()
                result['message_type'] = message_type

                # Unterschiedliche Message Types verarbeiten
                if message_type == 0x0001:  # ENUM_SESSIONS_REPLY
                    result.update(self._parse_enum_sessions_reply(br))
                elif message_type == 0x0002:  # SESSION_DESCRIPTION
                    result.update(self._parse_session_description(br))
                elif message_type == 0x0008:  # PLAYER_DATA
                    result.update(self._parse_player_data(br))

        except Exception as e:
            result['parse_warning'] = f"Partial parsing error: {str(e)}"

        return result

    def _parse_enum_sessions_reply(self, br: BinaryReader) -> dict:
        """Parse ENUM_SESSIONS_REPLY message"""
        result = {}

        try:
            if br.remaining_bytes() >= 4:
                # Session count
                session_count = br.read_uint32()
                result['session_count'] = session_count

                # Parse each session
                sessions = []
                for i in range(min(session_count, 10)):  # Limit für Sicherheit
                    if br.remaining_bytes() < 16:
                        break

                    session = {}

                    # Session GUID (16 bytes)
                    guid_bytes = br.read_bytes(16)
                    session['guid'] = guid_bytes.hex()

                    # Session name length und name
                    if br.remaining_bytes() >= 2:
                        name_length = br.read_uint16()
                        if br.remaining_bytes() >= name_length:
                            session['name'] = br.read_bytes(name_length).decode('utf-16le', errors='ignore').rstrip('\x00')

                    sessions.append(session)

                result['sessions'] = sessions
                if sessions:
                    result['name'] = sessions[0].get('name', 'DirectPlay Game')

        except Exception as e:
            result['enum_sessions_error'] = str(e)

        return result

    def _parse_session_description(self, br: BinaryReader) -> dict:
        """Parse SESSION_DESCRIPTION message"""
        result = {}

        try:
            if br.remaining_bytes() >= 8:
                # Max players
                max_players = br.read_uint32()
                current_players = br.read_uint32()

                result['max_players'] = max_players
                result['num_players'] = current_players

                # Session flags
                if br.remaining_bytes() >= 4:
                    flags = br.read_uint32()
                    result['password_protected'] = bool(flags & 0x1)
                    result['session_flags'] = flags

        except Exception as e:
            result['session_desc_error'] = str(e)

        return result

    def _parse_player_data(self, br: BinaryReader) -> dict:
        """Parse PLAYER_DATA message"""
        result = {}

        try:
            players = []

            # Player count
            if br.remaining_bytes() >= 4:
                player_count = br.read_uint32()
                result['num_players'] = player_count

                # Parse each player
                for i in range(min(player_count, 16)):  # Limit für Sicherheit
                    if br.remaining_bytes() < 8:
                        break

                    player = {}

                    # Player ID
                    player_id = br.read_uint32()
                    player['id'] = player_id

                    # Player name length
                    name_length = br.read_uint16()
                    if br.remaining_bytes() >= name_length:
                        # Player name (Unicode)
                        name_bytes = br.read_bytes(name_length)
                        player['name'] = name_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')

                    # Player flags/status
                    if br.remaining_bytes() >= 2:
                        player_flags = br.read_uint16()
                        player['ready'] = bool(player_flags & 0x1)
                        player['flags'] = player_flags

                    players.append(player)

                result['players'] = players

        except Exception as e:
            result['player_data_error'] = str(e)

        return result

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

    def _read_directplay_string(self, br: BinaryReader) -> str:
        """
        Liest einen DirectPlay-String (Unicode, length-prefixed).

        Args:
            br: BinaryReader instance

        Returns:
            str: Der gelesene String
        """
        if br.remaining_bytes() < 2:
            return ""

        length = br.read_uint16()
        if length == 0 or br.remaining_bytes() < length:
            return ""

        # DirectPlay verwendet oft UTF-16LE für Strings
        string_bytes = br.read_bytes(length)
        return string_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')

    def _read_cstring(self, br: BinaryReader, encoding: str = 'utf-8') -> str:
        """
        Liest einen null-terminierten C-String.

        Args:
            br: BinaryReader instance
            encoding: String encoding

        Returns:
            str: Der gelesene String
        """
        string_bytes = b''
        while br.remaining_bytes() > 0:
            byte = br.read_bytes(1)
            if byte == b'\x00':
                break
            string_bytes += byte

        return string_bytes.decode(encoding, errors='ignore')

    def _validate_directplay_magic(self, magic: bytes) -> bool:
        """
        Validiert DirectPlay Magic Bytes.

        Args:
            magic: Die ersten 4 Bytes des Pakets

        Returns:
            bool: True wenn gültiger DirectPlay Magic
        """
        # DirectPlay verwendet verschiedene Magic Values
        known_magic = [
            b'\x34\x00\xb0\xfa',  # Standard DirectPlay
            b'\x20\x00\x00\x00',  # Alternative DirectPlay
            b'\x10\x00\x00\x00',  # DirectPlay Session
        ]

        return magic in known_magic

    def _extract_game_guid(self, payload: bytes) -> str:
        """
        Extrahiert die Game GUID aus dem DirectPlay Payload.

        Args:
            payload: Das DirectPlay UDP Payload

        Returns:
            str: Die Game GUID als String oder leer bei Fehlern
        """
        try:
            # Game GUID ist bei Offset 28-43 (16 bytes)
            if len(payload) >= 44:
                guid_bytes = payload[28:44]
                # Konvertiere zu standard GUID Format
                return self._format_guid(guid_bytes)
        except Exception:
            pass

        return ""

    def _format_guid(self, guid_bytes: bytes) -> str:
        """
        Formatiert GUID Bytes zu Standard-GUID-String.

        Args:
            guid_bytes: 16 Bytes der GUID

        Returns:
            str: Formatierte GUID
        """
        if len(guid_bytes) != 16:
            return ""

        # Microsoft GUID Format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        return (f"{guid_bytes[0:4][::-1].hex()}-"
                f"{guid_bytes[4:6][::-1].hex()}-"
                f"{guid_bytes[6:8][::-1].hex()}-"
                f"{guid_bytes[8:10].hex()}-"
                f"{guid_bytes[10:16].hex()}")

    def _get_debug_info(self, buffer: bytes) -> dict:
        """
        Hilfsfunktion für Debugging - gibt detaillierte Paket-Informationen zurück.

        Args:
            buffer: Die rohen Antwortdaten

        Returns:
            dict: Debug-Informationen
        """
        debug_info = {
            'buffer_size': len(buffer),
            'buffer_hex': buffer[:100].hex() if len(buffer) > 100 else buffer.hex(),
            'ascii_preview': buffer[:50].decode('ascii', errors='replace') if len(buffer) > 0 else "",
        }

        if len(buffer) >= 4:
            magic = buffer[:4]
            debug_info['magic_hex'] = magic.hex()
            debug_info['magic_valid'] = self._validate_directplay_magic(magic)

        # Versuche Game GUID zu extrahieren
        if hasattr(self, '_build_query_packet'):
            try:
                query_packet = self._build_query_packet()
                debug_info['game_guid'] = self._extract_game_guid(query_packet)
            except Exception:
                pass

        return debug_info

    def _extract_version_info(self, buffer: bytes) -> dict:
        """
        Extrahiert Version-Informationen aus DirectPlay-Paketen.

        Args:
            buffer: Die rohen Antwortdaten

        Returns:
            dict: Version-Informationen
        """
        version_info = {}

        if len(buffer) < 52:
            return version_info

        try:
            # Magic Number Analysis (TCP Response)
            magic = int.from_bytes(buffer[0:4], 'little')
            version_info['magic_number'] = f"0x{magic:08x}"

            # Bekannte Magic Numbers für verschiedene Versionen
            known_versions = {
                0x8e00b0fa: "Age of Empires 1.0c",
                0x8800b0fa: "Age of Empires II 2.0a",
                0x3400b0fa: "DirectPlay Query"
            }

            if magic in known_versions:
                version_info['detected_version'] = known_versions[magic]

            # UDP Query Version ID (wenn verfügbar im Original Query)
            if hasattr(self, '_build_query_packet'):
                try:
                    query_packet = self._build_query_packet()
                    if len(query_packet) >= 52:
                        udp_version_id = int.from_bytes(query_packet[48:52], 'little')
                        version_info['udp_version_id'] = udp_version_id

                        # Bekannte UDP Version IDs
                        udp_versions = {
                            1: "Age of Empires 1.0",
                            17: "Age of Empires II 2.0"
                        }

                        if udp_version_id in udp_versions:
                            version_info['game_version'] = udp_versions[udp_version_id]
                except Exception:
                    pass

            # Session Data Version Analysis (Offset 84)
            if len(buffer) >= 88:
                session_version = int.from_bytes(buffer[84:88], 'little')
                version_info['session_version'] = session_version

                # Charakteristische Session Version Values
                if session_version == 567281:  # 0x0008a7f1
                    version_info['likely_version'] = "Age of Empires 1.0c"
                elif session_version == 2274156:  # 0x0022b36c
                    version_info['likely_version'] = "Age of Empires II 2.0a"

        except Exception as e:
            version_info['version_error'] = str(e)

        return version_info
