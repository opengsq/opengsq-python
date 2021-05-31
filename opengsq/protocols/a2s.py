import bz2
import zlib

from opengsq.interfaces import IProtocol
from opengsq.protocols.binary_reader import BinaryReader
from opengsq.protocols.socket_async import SocketAsync


class A2S(IProtocol):
    full_name = 'A2S Protocol'

    # Requests (https://developer.valvesoftware.com/wiki/Server_queries#Requests)
    class __Request():
        A2S_INFO = b'TSource Engine Query\x00'
        A2S_PLAYER = b'\x55'
        A2S_RULES = b'\x56'
        A2A_PING = b'\x69'
        A2S_SERVERQUERY_GETCHALLENGE = b'\x57'

    class __Response():
        S2A_INFO_SRC = 0x49
        S2A_INFO_DETAILED = 0x6D
        S2A_PLAYER = 0x44
        S2A_RULES = 0x45
        A2A_ACK = 0x6A
        S2C_CHALLENGE = 0x41

    __PACKET_HEADER = b'\xFF\xFF\xFF\xFF'

    GOLDSOURCE = "GOLDSOURCE"
    SOURCE = "SOURCE"

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0, engine: str = SOURCE):
        self.__sock = None
        self.__address = address
        self.__query_port = query_port
        self.__timeout = timeout
        self.__engine = engine.upper()

    def __del__(self):
        self.__disconnect()

    async def __connect(self):
        self.__disconnect()
        self.__sock = SocketAsync()
        self.__sock.settimeout(self.__timeout)
        await self.__sock.connect((SocketAsync.gethostbyname(self.__address), self.__query_port))

    def __disconnect(self):
        if self.__sock:
            self.__sock.close()

    # A2S_INFO (https://developer.valvesoftware.com/wiki/Server_queries#A2S_INFO)
    async def get_info(self) -> dict:
        await self.__connect()
        header, br = await self.__challenge_request(data=self.__Request.A2S_INFO)
        self.__disconnect()

        if header != self.__Response.S2A_INFO_SRC and header != self.__Response.S2A_INFO_DETAILED:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {} or {}.'
                .format(chr(header), chr(self.__Response.S2A_INFO_SRC), chr(self.__Response.S2A_INFO_DETAILED))
            )

        info = {}

        if header == self.__Response.S2A_INFO_SRC:
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

        # Obsolete GoldSource Response
        elif header == self.__Response.S2A_INFO_DETAILED:
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

    # A2S_PLAYER (https://developer.valvesoftware.com/wiki/Server_queries#A2S_PLAYER)
    async def get_players(self) -> list:
        await self.__connect()
        header, br = await self.__challenge_request(data=self.__Request.A2S_PLAYER, challenge=self.__PACKET_HEADER)
        self.__disconnect()

        if header != self.__Response.S2A_PLAYER:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self.__Response.S2A_PLAYER))
            )

        player_count = br.read_byte()
        players = []

        while player_count > 0 and len(br.read()) > 0:
            player_count -= 1
            player = {}
            player['Index'] = br.read_byte()
            player['Name'] = br.read_string()
            player['Score'] = br.read_long()
            player['Duration'] = br.read_float()
            players.append(player)

        return players

    # A2S_RULES (https://developer.valvesoftware.com/wiki/Server_queries#A2S_RULES)
    async def get_rules(self) -> list:
        await self.__connect()
        header, br = await self.__challenge_request(data=self.__Request.A2S_RULES, challenge=self.__PACKET_HEADER)
        self.__disconnect()

        if header != self.__Response.S2A_RULES:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self.__Response.S2A_RULES))
            )

        rule_count = br.read_short()
        rules = []

        while rule_count > 0 and len(br.read()) > 0:
            rule_count -= 1
            rule = {}
            rule['Name'] = br.read_string()
            rule['Value'] = br.read_string()
            rules.append(rule)

        return rules

    # A2A_PING (https://developer.valvesoftware.com/wiki/Server_queries#A2A_PING)
    async def get_ping(self) -> bool:
        await self.__connect()

        self.__write(self.__PACKET_HEADER + self.__Request.A2A_PING)
        br = BinaryReader(data=await self.__read())
        self.__disconnect()

        header = br.read_byte()

        return header == self.__Response.A2A_ACK

    # A2S_SERVERQUERY_GETCHALLENGE (https://developer.valvesoftware.com/wiki/Server_queries#A2S_SERVERQUERY_GETCHALLENGE)
    async def get_challenge(self) -> bytes:
        await self.__connect()

        self.__write(self.__PACKET_HEADER + self.__Request.A2S_SERVERQUERY_GETCHALLENGE)
        br = BinaryReader(data=await self.__read())
        self.__disconnect()

        header = br.read_byte()

        if header != self.__Response.S2C_CHALLENGE:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self.__Response.S2C_CHALLENGE))
            )

        return br.read()

    def __write(self, data):
        self.__sock.send(data)

    # TODO: Make it cleaner
    async def __read(self) -> bytes:
        br = BinaryReader(data=await self.__sock.recv())
        header = br.read_long()

        if header == -1:
            return br.read()

        payloads = {}
        request_id = br.read_long()

        # Multi-packet Response Format - (https://developer.valvesoftware.com/wiki/Server_queries#Goldsource_Server)
        if self.__engine == self.GOLDSOURCE:
            packet_metadata = br.read_byte()
            total = packet_metadata & 0x0F
            number = packet_metadata >> 4
            payloads[number] = br.read()

            while len(payloads) < total:
                br = BinaryReader(data=await self.__sock.recv())

                if br.read_long() == -2 and br.read_long() == request_id:
                    packet_metadata = br.read_byte()
                    number = packet_metadata >> 4
                    payloads[number] = br.read()

            response = b''.join(payloads[number] for number in sorted(payloads))

        # Multi-packet Response Format - (https://developer.valvesoftware.com/wiki/Server_queries#Source_Server)
        else:
            total = br.read_byte()
            number = br.read_byte()
            is_compressed = (request_id & 0x80000000) != 0

            if is_compressed:
                br.read_long()
                checksum = br.read_long()
            else:
                br.read_short()

            payloads[number] = br.read()

            while len(payloads) < total:
                br = BinaryReader(data=await self.__sock.recv())

                if br.read_long() == -2 and br.read_long() == request_id:
                    br.read_byte()
                    number = br.read_byte()
                    br.read_short()
                    payloads[number] = br.read()

            response = b''.join(payloads[number] for number in sorted(payloads))

            if is_compressed:
                response = bz2.decompress(response)

                if zlib.crc32(response) != checksum:
                    raise InvalidPacketException('CRC32 checksum mismatch of uncompressed packet data.')

        return response.startswith(self.__PACKET_HEADER) and response[4:] or response

    async def __challenge_request(self, data: bytes, challenge: bytes = b''):
        self.__write(self.__PACKET_HEADER + data + challenge)
        br = BinaryReader(data=await self.__read())
        header = br.read_byte()

        # Some servers will bypass replying with a challenge
        if header == self.__Response.S2C_CHALLENGE:
            self.__write(self.__PACKET_HEADER + data + br.read())
            br = BinaryReader(data=await self.__read())
            header = br.read_byte()

        return header, br


class InvalidPacketException(Exception):
    pass
