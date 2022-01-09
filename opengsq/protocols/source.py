import bz2
import zlib

from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class Source(ProtocolBase):
    full_name = 'Source Engine Query Protocol'
    _challenge = ''

    class __RequestHeader():
        A2S_INFO = b'\x54Source Engine Query\0'
        A2S_PLAYER = b'\x55'
        A2S_RULES = b'\x56'
        A2A_PING = b'\x69'
        A2S_SERVERQUERY_GETCHALLENGE = b'\x57'

    class __ResponseHeader():
        S2C_CHALLENGE = 0x41
        S2A_INFO_SRC = 0x49
        S2A_INFO_DETAILED = 0x6D
        S2A_PLAYER = 0x44
        S2A_RULES = 0x45
        A2A_ACK = 0x6A
        
    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address, query_port, timeout)

    # Retrieves information about the server including, but not limited to: its name, the map currently being played, and the number of players.
    # See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_INFO
    async def get_info(self) -> dict:
        response_data = await self.__connect_and_send_challenge(self.__RequestHeader.A2S_INFO)
        
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

    # This query retrieves information about the players currently on the server.
    # See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_INFO
    async def get_players(self) -> list:
        response_data = await self.__connect_and_send_challenge(self.__RequestHeader.A2S_PLAYER)
        
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

    # Returns the server rules, or configuration variables in name/value pairs.
    # See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_RULES
    async def get_rules(self) -> dict:
        response_data = await self.__connect_and_send_challenge(self.__RequestHeader.A2S_RULES)
        
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
        sock = SocketAsync()
        sock.settimeout(self._timeout)
        await sock.connect((self._address, self._query_port))
        
        # Send and receive
        request_base = b'\xFF\xFF\xFF\xFF' + header
        request_data = request_base

        if len(self._challenge) > 0:
            request_data += self._challenge
        elif header != self.__RequestHeader.A2S_INFO:
            request_data += b'\xFF\xFF\xFF\xFF'

        sock.send(request_data)
        response_data = await self.__receive(sock)
        br = BinaryReader(response_data)
        header = br.read_byte()

        # The server may reply with a challenge
        if header == self.__ResponseHeader.S2C_CHALLENGE:
            self._challenge = br.read()
            
            # Send the challenge and receive
            sock.send(request_base + self._challenge)
            response_data = await self.__receive(sock)
            
        sock.close()

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


class InvalidPacketException(Exception):
    pass


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        source = Source(address='45.147.5.5', query_port=27015, timeout=5.0)
        info = await source.get_info()
        players = await source.get_players()
        rules = await source.get_rules()
        print(json.dumps(info, indent=None, ensure_ascii=False) + '\n')
        print(json.dumps(players, indent=None, ensure_ascii=False) + '\n')
        print(json.dumps(rules, indent=None, ensure_ascii=False) + '\n')

    asyncio.run(main_async())
