from __future__ import annotations

import re

from opengsq.responses.warfork import Player
from opengsq.responses.quake2 import Status
from opengsq.binary_reader import BinaryReader
from opengsq.protocols.quake3 import Quake3


class Warfork(Quake3):
    """
    This class represents the Quake3 Protocol for Warfork. It provides methods to interact with the Warfork API.
    """

    full_name = "Warfork Protocol"
 
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        """
        Initializes the Quake3 object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param timeout: The timeout for the server connection.
        """
        super().__init__(host, port, timeout)
 
    async def get_status(self, strip_color=True) -> Status:
        br = await self._get_response_binary_reader()

        status = Status(info=self._parse_info(br), players=self._parse_players(br))
        if not strip_color:
            return status

        if "sv_hostname" in status.info:
            status.info["sv_hostname"] = Quake3.strip_colors(status.info["sv_hostname"])

        for player in status.players:
            if player.name:
                player.name = Quake3.strip_colors(player.name)

        return status
 
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
                team=int(matches[3]) if len(matches) > 3 else 0,
            )
            players.append(player)

        return players


if __name__ == "__main__":
    import asyncio

    async def main_async():
        quake3 = Quake3(host="108.61.18.110", port=27960, timeout=5.0)
        info = await quake3.get_info()
        print(info)
        status = await quake3.get_status()
        print(status)

    asyncio.run(main_async())
