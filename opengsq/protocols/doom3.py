import re

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class Doom3(ProtocolBase):
    """Doom3 Protocol"""
    full_name = 'Doom3 Protocol'

    _player_fields = {
        'doom': ['id', 'ping', 'rate', 'name'],
        'quake4': ['id', 'ping', 'rate', 'name', 'clantag'],
        'etqw': ['id', 'ping', 'name', 'clantag_pos', 'clantag', 'typeflag']
    }

    async def get_info(self, strip_color=True):
        request = b'\xFF\xFFgetInfo\x00ogsq\x00'
        response = await SocketAsync.send_and_receive(self._address, self._query_port, self._timeout, request)

        # Remove the first two 0xFF
        br = BinaryReader(response[2:])
        header = br.read_string()

        if header != 'infoResponse':
            raise InvalidPacketException(f'Packet header mismatch. Received: {header}. Expected: infoResponse.')

        # Read challenge
        br.read_bytes(4)

        if br.read_bytes(4) != b'\xff\xff\xff\xff':
            br.stream_position -= 4

        info = {}

        # Read protocol version
        minor = br.read_short()
        major = br.read_short()
        info['version'] = f'{major}.{minor}'

        # Read packet size
        if br.read_long() != br.length():
            br.stream_position -= 4

        # Key / value pairs, delimited by an empty pair
        while br.length() > 0:
            key = br.read_string().strip()
            val = br.read_string().strip()

            if key == '' and val == '':
                break

            info[key] = Doom3.strip_colors(val) if strip_color else val

        stream_position = br.stream_position

        # Try parse the fields
        for mod in self._player_fields.keys():
            try:
                info['players'] = self.__parse_player(br, self._player_fields[mod], strip_color)
                break
            except Exception:
                info['players'] = []
                br.stream_position = stream_position

        return info

    def __parse_player(self, br: BinaryReader, fields: list, strip_color: bool):
        players = []

        def value_by_field(field: str, br: BinaryReader):
            if field == 'id' or field == 'clantag_pos' or field == 'typeflag':
                return br.read_byte()
            elif field == 'ping':
                return br.read_short()
            elif field == 'rate':
                return br.read_long()

            string = br.read_string()

            return Doom3.strip_colors(string) if strip_color else string

        while True:
            player = {field: value_by_field(field, br) for field in fields}

            if player['id'] == 32:
                break

            players.append(player)

        return players

    @staticmethod
    def strip_colors(text: str):
        """Strip color codes"""
        return re.compile('\\^(X.{6}|.)').sub('', text)


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        # doom3
        doom3 = Doom3(address='66.85.14.240', query_port=27666, timeout=5.0)
        info = await doom3.get_info()
        print(json.dumps(info, indent=None) + '\n')

        # etqw
        doom3 = Doom3(address='178.162.135.83', query_port=27735, timeout=5.0)
        info = await doom3.get_info()
        print(json.dumps(info, indent=None) + '\n')

        # quake4
        doom3 = Doom3(address='88.99.0.7', query_port=28007, timeout=5.0)
        info = await doom3.get_info()
        print(json.dumps(info, indent=None) + '\n')

    asyncio.run(main_async())
