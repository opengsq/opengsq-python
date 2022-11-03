import bz2
import random
import zlib
from enum import Enum

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import AuthenticationException, InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync, SocketKind


class Source(ProtocolBase):
    """Source Engine Protocol"""
    full_name = 'Source Engine Protocol'

    _A2S_INFO = b'\x54Source Engine Query\0'
    _A2S_PLAYER = b'\x55'
    _A2S_RULES = b'\x56'

    class __RequestHeader():
        A2A_PING = b'\x69'
        A2S_SERVERQUERY_GETCHALLENGE = b'\x57'

    class __ResponseHeader():
        S2C_CHALLENGE = 0x41
        S2A_INFO_SRC = 0x49
        S2A_INFO_DETAILED = 0x6D
        S2A_PLAYER = 0x44
        S2A_RULES = 0x45
        A2A_ACK = 0x6A

    async def get_info(self) -> dict:
        """
        Retrieves information about the server including,
        but not limited to: its name, the map currently being played, and the number of players.

        See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_INFO
        """
        response_data = await self.__connect_and_send_challenge(self._A2S_INFO)

        br = BinaryReader(response_data)
        header = br.read_byte()

        if header != self.__ResponseHeader.S2A_INFO_SRC and header != self.__ResponseHeader.S2A_INFO_DETAILED:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {} or {}.'
                .format(chr(header), chr(self.__ResponseHeader.S2A_INFO_SRC), chr(self.__ResponseHeader.S2A_INFO_DETAILED))
            )

        if header == self.__ResponseHeader.S2A_INFO_SRC:
            return self.__parse_from_info_src(br)

        # Obsolete GoldSource Response
        return self.__parse_from_info_detailed(br)

    def __parse_from_info_src(self, br: BinaryReader) -> dict:
        info = {}
        info['Protocol'] = br.read_byte()
        info['Name'] = br.read_string()
        info['Map'] = br.read_string()
        info['Folder'] = br.read_string()
        info['Game'] = br.read_string()
        info['ID'] = br.read_short()
        info['Players'] = br.read_byte()
        info['MaxPlayers'] = br.read_byte()
        info['Bots'] = br.read_byte()
        info['ServerType'] = chr(br.read_byte())
        info['Environment'] = chr(br.read_byte())
        info['Visibility'] = br.read_byte()
        info['VAC'] = br.read_byte()

        # These fields only exist in a response if the server is running The Ship
        if info['ID'] == 2400:
            info['Mode'] = br.read_byte()
            info['Witnesses'] = br.read_byte()
            info['Duration'] = br.read_byte()

        info['Version'] = br.read_string()
        info['EDF'] = br.read_byte()

        if info['EDF'] & 0x80:
            info['GamePort'] = br.read_short()

        if info['EDF'] & 0x10:
            info['SteamID'] = br.read_long_long()

        if info['EDF'] & 0x40:
            info['SpecPort'] = br.read_short()
            info['SpecName'] = br.read_string()

        if info['EDF'] & 0x20:
            info['Keywords'] = br.read_string()

        if info['EDF'] & 0x01:
            info['GameID'] = br.read_long_long()

        return info

    def __parse_from_info_detailed(self, br: BinaryReader) -> dict:
        info = {}
        info['Address'] = br.read_string()
        info['Name'] = br.read_string()
        info['Map'] = br.read_string()
        info['Folder'] = br.read_string()
        info['Game'] = br.read_string()
        info['Players'] = br.read_byte()
        info['MaxPlayers'] = br.read_byte()
        info['Protocol'] = br.read_byte()
        info['ServerType'] = chr(br.read_byte())
        info['Environment'] = chr(br.read_byte())
        info['Visibility'] = br.read_byte()
        info['Mod'] = br.read_byte()

        if info['Mod'] == 1:
            info['Link'] = br.read_string()
            info['DownloadLink'] = br.read_string()

            br.read_byte()

            info['Version'] = br.read_long()
            info['Size'] = br.read_long()
            info['Type'] = br.read_byte()
            info['DLL'] = br.read_byte()

        info['VAC'] = br.read_byte()
        info['Bots'] = br.read_byte()

        return info

    async def get_players(self) -> list:
        """
        This query retrieves information about the players currently on the server.

        See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_PLAYER
        """
        response_data = await self.__connect_and_send_challenge(self._A2S_PLAYER)

        br = BinaryReader(response_data)
        header = br.read_byte()

        if header != self.__ResponseHeader.S2A_PLAYER:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self.__ResponseHeader.S2A_PLAYER))
            )

        player_count = br.read_byte()
        players = []

        for _ in range(player_count):
            br.read_byte()

            player = {}
            player['Name'] = br.read_string()
            player['Score'] = br.read_long()
            player['Duration'] = br.read_float()
            players.append(player)

        if br.length() > 0:
            for i in range(player_count):
                players[i]['Deaths'] = br.read_long()
                players[i]['Money'] = br.read_long()

        return players

    async def get_rules(self) -> dict:
        """
        Returns the server rules, or configuration variables in name/value pairs.

        See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_RULES
        """
        response_data = await self.__connect_and_send_challenge(self._A2S_RULES)

        br = BinaryReader(response_data)
        header = br.read_byte()

        if header != self.__ResponseHeader.S2A_RULES:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self.__ResponseHeader.S2A_RULES))
            )

        rule_count = br.read_short()
        rules = dict((br.read_string(), br.read_string()) for _ in range(rule_count))

        return rules

    async def __connect_and_send_challenge(self, header: __RequestHeader) -> bytes:
        # Connect to remote host
        with SocketAsync() as sock:
            sock.settimeout(self._timeout)
            await sock.connect((self._address, self._query_port))

            # Send and receive
            request_base = b'\xFF\xFF\xFF\xFF' + header
            request_data = request_base

            if header != self._A2S_INFO:
                request_data += b'\xFF\xFF\xFF\xFF'

            sock.send(request_data)

            # Retries 3 times, some servers require multiple challenges
            for _ in range(3):
                response_data = await self.__receive(sock)
                br = BinaryReader(response_data)
                header = br.read_byte()

                # The server response with a challenge
                if header == self.__ResponseHeader.S2C_CHALLENGE:
                    challenge = br.read()

                    # Send the challenge and receive
                    sock.send(request_base + challenge)
                else:
                    break

        return response_data

    async def __receive(self, sock: SocketAsync) -> bytes:
        total_packets = -1
        payloads = dict()
        packets = list()

        while True:
            response_data = await sock.recv()
            packets.append(response_data)

            br = BinaryReader(response_data)
            header = br.read_long()

            # Simple Response Format
            if header == -1:
                # Return the payload
                return br.read()

            # Packet id
            id = br.read_long()
            is_compressed = (id & 0x80000000) < 0

            # Check is GoldSource multi-packet response format
            if self.__is_gold_source_split(BinaryReader(br.read())):
                return await self.__parse_gold_source_packet(sock, packets)

            # The total number of packets
            total_packets = br.read_byte()

            # The number of the packet
            number = br.read_byte()

            # Packet size
            br.read_short()

            if number == 0 and is_compressed:
                # Decompressed size
                br.read_long()

                # CRC32 sum
                crc32_checksum = br.read_long()

            payloads[number] = br.read()

            if total_packets == -1 or len(payloads) < total_packets:
                continue

            break

        # Combine the payloads
        combined_payload = b''.join(payloads[number] for number in sorted(payloads))

        # Decompress the payload
        if is_compressed:
            combined_payload = bz2.decompress(combined_payload)

            # Check CRC32 sum
            if zlib.crc32(combined_payload) != crc32_checksum:
                raise InvalidPacketException('CRC32 checksum mismatch of uncompressed packet data.')

        return combined_payload.startswith(b'\xFF\xFF\xFF\xFF') and combined_payload[4:] or combined_payload

    def __is_gold_source_split(self, br: BinaryReader):
        # Upper 4 bits represent the number of the current packet (starting at 0)
        number = br.read_byte() >> 4

        # Check is it Gold Source packet split format
        return number == 0 and br.read().startswith(b'\xFF\xFF\xFF\xFF')

    async def __parse_gold_source_packet(self, sock: SocketAsync, packets: list):
        total_packets = -1
        payloads = dict()

        while total_packets == -1 or len(payloads) < total_packets:
            # Load the old received packets first, then receive the packets
            if len(payloads) < len(packets):
                response_data = packets[len(payloads)]
            else:
                response_data = await sock.recv()

            br = BinaryReader(response_data)

            # Header
            br.read_long()

            # Packet id
            br.read_long()

            # The total number of packets
            total_packets = br.read_byte()

            # Upper 4 bits represent the number of the current packet (starting at 0)
            number = total_packets >> 4

            # Bottom 4 bits represent the total number of packets (2 to 15)
            total_packets &= 0x0F

            payloads[number] = br.read()

        # Combine the payloads
        combined_payload = b''.join(payloads[number] for number in sorted(payloads))

        return combined_payload.startswith(b'\xFF\xFF\xFF\xFF') and combined_payload[4:] or combined_payload

    class RemoteConsole(ProtocolBase):
        """Source RCON Protocol"""

        full_name = 'Source RCON Protocol'

        def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
            """Source RCON Protocol"""
            super().__init__(address, query_port, timeout)

            self._sock = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.close()

        def close(self):
            """Close the connection"""
            if self._sock:
                self._sock.close()

        async def authenticate(self, password: str):
            """Authenticate the connection"""

            # Connect
            self._sock = SocketAsync(SocketKind.SOCK_STREAM)
            self._sock.settimeout(self._timeout)
            await self._sock.connect((self._address, self._query_port))

            # Send password
            id = random.randrange(4096)
            self._sock.send(self.__Packet(id, self.__PacketType.SERVERDATA_AUTH.value, password).get_bytes())

            # Receive and parse as Packet
            response_data = await self._sock.recv()
            packet = self.__Packet(response_data)

            # Sometimes it will return a PacketType.SERVERDATA_RESPONSE_VALUE, so receive again
            if packet.type != self.__PacketType.SERVERDATA_AUTH_RESPONSE.value:
                response_data = await self._sock.recv()
                packet = self.__Packet(response_data)

            # Throw exception if not PacketType.SERVERDATA_AUTH_RESPONSE
            if packet.type != self.__PacketType.SERVERDATA_AUTH_RESPONSE.value:
                self._sock.close()
                raise InvalidPacketException(
                    'Packet header mismatch. Received: {}. Expected: {}.'
                    .format(chr(packet.type), chr(self.__PacketType.SERVERDATA_AUTH_RESPONSE.value))
                )

            # Throw exception if authentication failed
            if packet.id == -1 or packet.id != id:
                self._sock.close()
                raise AuthenticationException('Authentication failed')

        async def send_command(self, command: str):
            """Send command to the server"""

            # Send the command and a empty command packet
            id = random.randrange(4096)
            dummy_id = id + 1
            self._sock.send(self.__Packet(id, self.__PacketType.SERVERDATA_EXECCOMMAND.value, command).get_bytes())
            self._sock.send(self.__Packet(dummy_id, self.__PacketType.SERVERDATA_EXECCOMMAND.value, '').get_bytes())

            packet_bytes = bytes([])
            response = ''

            while True:
                # Receive
                response_data = await self._sock.recv()

                # Concat to last unused bytes
                packet_bytes += response_data

                # Get the packets and get the unused bytes
                packets, packet_bytes = self.__get_packets(packet_bytes)

                # Loop all packets
                for packet in packets:
                    if packet.id == dummy_id:
                        return response

                    response += packet.body

        # Handle Multiple-packet Responses
        def __get_packets(self, packet_bytes: bytes):
            packets = []

            br = BinaryReader(packet_bytes)

            # + 4 to ensure br.ReadInt32() is readable
            while br.stream_position + 4 < len(packet_bytes):
                size = br.read_long()

                if br.stream_position + size > len(packet_bytes):
                    return packets, packet_bytes[br.stream_position - 4:]

                id = br.read_long()
                type = br.read_long()
                body = br.read_string()
                br.read_byte()

                packets.append(self.__Packet(id, type, body))

            return packets, bytes([])

        class __PacketType(Enum):
            SERVERDATA_AUTH = 3
            SERVERDATA_AUTH_RESPONSE = 2
            SERVERDATA_EXECCOMMAND = 2
            SERVERDATA_RESPONSE_VALUE = 0

        class __Packet:
            def __init__(self, *args):
                if len(args) == 3:
                    self.id = args[0]
                    self.type = args[1]
                    self.body = args[2]
                else:
                    # Single-packet Responses
                    br = BinaryReader(args[0])
                    br.read_long()
                    self.id = br.read_long()
                    self.type = br.read_long()
                    self.body = br.read_string()

            def get_bytes(self):
                packet_bytes = self.id.to_bytes(4, byteorder='little')
                packet_bytes += self.type.to_bytes(4, byteorder='little')
                packet_bytes += str.encode(self.body + '\0')
                return len(packet_bytes).to_bytes(4, byteorder='little') + packet_bytes


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        source = Source(address='209.205.114.187', query_port=27015, timeout=5.0)
        info = await source.get_info()
        print(json.dumps(info, indent=None, ensure_ascii=False) + '\n')
        players = await source.get_players()
        print(json.dumps(players, indent=None, ensure_ascii=False) + '\n')
        rules = await source.get_rules()
        print(json.dumps(rules, indent=None, ensure_ascii=False) + '\n')

    asyncio.run(main_async())
