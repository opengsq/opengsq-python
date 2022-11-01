import re

from opengsq.binary_reader import BinaryReader
from opengsq.protocols.quake1 import Quake1


class Quake2(Quake1):
    """Quake2 Protocol"""
    full_name = 'Quake2 Protocol'

    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        """Quake2 Query Protocol"""
        super().__init__(address, query_port, timeout)
        self._response_header = 'print\n'

    def _parse_players(self, br: BinaryReader) -> list:
        players = []

        for matches in self._get_player_match_collections(br):
            matches: list[re.Match] = [match.group() for match in matches]

            player = {
                'frags': int(matches[0]),
                'ping': int(matches[1]),
            }

            if len(matches) > 2:
                player['name'] = str(matches[2]).strip('"')

            if len(matches) > 3:
                player['address'] = str(matches[3]).strip('"')

            players.append(player)

        return players


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        quake2 = Quake2(address='46.165.236.118', query_port=27910, timeout=5.0)
        status = await quake2.get_status()
        print(json.dumps(status, indent=None) + '\n')

    asyncio.run(main_async())
