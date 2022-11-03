import struct

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class Samp(ProtocolBase):
    """San Andreas Multiplayer Protocol"""
    full_name = 'San Andreas Multiplayer Protocol'

    _request_header = b'SAMP'
    _response_header = b'SAMP'

    async def get_status(self):
        br = await self.__send_and_receive(b'i')

        result = {}
        result['password'] = br.read_byte()
        result['numplayers'] = br.read_short()
        result['maxplayers'] = br.read_short()
        result['servername'] = self.__read_string(br, 4)
        result['gametype'] = self.__read_string(br, 4)
        result['language'] = self.__read_string(br, 4)

        return result

    async def get_players(self):
        """Server may not response when numplayers > 100"""
        br = await self.__send_and_receive(b'd')
        players = []
        numplayers = br.read_short()

        for _ in range(numplayers):
            player = {}
            player['id'] = br.read_byte()
            player['name'] = self.__read_string(br)
            player['score'] = br.read_long()
            player['ping'] = br.read_long()
            players.append(player)

        return players

    async def get_rules(self):
        br = await self.__send_and_receive(b'r')
        numrules = br.read_short()

        return dict((self.__read_string(br), self.__read_string(br)) for _ in range(numrules))

    async def __send_and_receive(self, data: bytes):
        # Format the address
        host = SocketAsync.gethostbyname(self._address)
        packet_header = struct.pack('BBBBH', *map(int, host.split('.') + [self._query_port])) + data
        request = self._request_header + packet_header

        # Validate the response
        response = await SocketAsync.send_and_receive(self._address, self._query_port, self._timeout, request)
        header = response[:len(self._response_header)]

        if header != self._response_header:
            raise InvalidPacketException(f'Packet header mismatch. Received: {header}. Expected: {self._response_header}.')

        return BinaryReader(response[len(self._response_header) + len(packet_header):])

    def __read_string(self, br: BinaryReader, read_offset=1):
        length = br.read_byte() if read_offset == 1 else br.read_long()
        return str(br.read_bytes(length), encoding='utf-8', errors='ignore')


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        samp = Samp(address='51.254.178.238', query_port=7777, timeout=5.0)
        status = await samp.get_status()
        print(json.dumps(status, indent=None) + '\n')
        players = await samp.get_players()
        print(json.dumps(players, indent=None) + '\n')
        rules = await samp.get_rules()
        print(json.dumps(rules, indent=None) + '\n')

    asyncio.run(main_async())
