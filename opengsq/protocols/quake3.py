import re

from opengsq.binary_reader import BinaryReader
from opengsq.protocols.quake2 import Quake2


class Quake3(Quake2):
    """Quake3 Protocol"""
    full_name = 'Quake3 Protocol'

    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        """Quake3 Query Protocol"""
        super().__init__(address, query_port, timeout)
        self._request_header = b'getstatus'
        self._response_header = 'statusResponse\n'

    async def get_info(self, strip_color=True) -> dict:
        """This returns server information only."""
        response_data = await self._connect_and_send(b'getinfo opengsq')

        br = BinaryReader(response_data)
        header = br.read_string(self._delimiter1)
        response_header = 'infoResponse\n'

        if header != response_header:
            raise Exception(f'Packet header mismatch. Received: {header}. Expected: {response_header}.')

        info = self._parse_info(br)

        if not strip_color:
            return info

        if 'hostname' in info:
            info['hostname'] = Quake3.strip_colors(info['hostname'])

        return info

    async def get_status(self, strip_color=True) -> dict:
        """This returns server information and players."""
        br = await self._get_response_binary_reader()

        status = {
            'info': self._parse_info(br),
            'players': self._parse_players(br),
        }

        if not strip_color:
            return status

        if 'sv_hostname' in status['info']:
            status['info']['sv_hostname'] = Quake3.strip_colors(status['info']['sv_hostname'])

        for player in status['players']:
            if 'name' in player:
                player['name'] = Quake3.strip_colors(player['name'])

        return status

    @staticmethod
    def strip_colors(text: str):
        """Strip color codes"""
        return re.compile('\\^(X.{6}|.)').sub('', text)


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        quake3 = Quake3(address='85.10.197.106', query_port=27960, timeout=5.0)
        info = await quake3.get_info()
        status = await quake3.get_status()
        print(json.dumps(info, indent=None) + '\n')
        print(json.dumps(status, indent=None) + '\n')

    asyncio.run(main_async())
