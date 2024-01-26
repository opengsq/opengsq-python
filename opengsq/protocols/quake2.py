from __future__ import annotations

import re

from opengsq.responses.quake2 import Player, Status
from opengsq.binary_reader import BinaryReader
from opengsq.protocols.quake1 import Quake1


class Quake2(Quake1):
    """
    This class represents the Quake2 Protocol. It provides methods to interact with the Quake2 API.
    """

    full_name = "Quake2 Protocol"

    def __init__(self, host: str, port: int, timeout: float = 5.0):
        """
        Initializes the Quake2 Query Protocol.

        :param host: The host of the game server.
        :param port: The port of the game server.
        :param timeout: The timeout for the connection. Defaults to 5.0.
        """
        super().__init__(host, port, timeout)
        self._response_header = "print\n"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        br = await self._get_response_binary_reader()
        return Status(info=self._parse_info(br), players=self._parse_players(br))

    def _parse_players(self, br: BinaryReader):
        """
        Parses the players from the given BinaryReader object.

        :param br: The BinaryReader object to parse the players from.
        :return: A list containing the players.
        """
        players = []

        for matches in self._get_player_match_collections(br):
            matches: list[re.Match] = [match.group() for match in matches]

            player = Player(
                frags=int(matches[0]),
                ping=int(matches[1]),
                name=str(matches[2]).strip('"') if len(matches) > 2 else "",
                address=str(matches[3]).strip('"') if len(matches) > 3 else "",
            )

            players.append(player)

        return players


if __name__ == "__main__":
    import asyncio

    async def main_async():
        quake2 = Quake2(host="46.165.236.118", port=27910, timeout=5.0)
        status = await quake2.get_status()
        print(status)

    asyncio.run(main_async())
