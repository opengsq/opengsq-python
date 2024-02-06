from __future__ import annotations

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.ase import Player, Status


class ASE(ProtocolBase):
    """
    This class represents the All-Seeing Eye Protocol. It provides methods to interact with the All-Seeing Eye API.
    """

    full_name = "All-Seeing Eye Protocol"

    _request = b"s"
    _response = b"EYE1"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        This method sends a request to the server and parses the response to create a Status object.

        :return: The status of the game server.
        """
        response = await UdpClient.communicate(self, self._request)

        br = BinaryReader(response)
        header = br.read_bytes(4)
        InvalidPacketException.throw_if_not_equal(header, self._response)

        return Status(
            game_name=br.read_pascal_string(),
            game_port=int(br.read_pascal_string()),
            hostname=br.read_pascal_string(),
            game_type=br.read_pascal_string(),
            map=br.read_pascal_string(),
            version=br.read_pascal_string(),
            password=br.read_pascal_string() != "0",
            num_players=int(br.read_pascal_string()),
            max_players=int(br.read_pascal_string()),
            rules=self.__parse_rules(br),
            players=self.__parse_players(br),
        )

    def __parse_rules(self, br: BinaryReader) -> dict[str, str]:
        rules = {}

        while not br.is_end():
            key = br.read_pascal_string()

            if not key:
                break

            rules[key] = br.read_pascal_string()

        return rules

    def __parse_players(self, br: BinaryReader) -> list[Player]:
        players: list[Player] = []

        while not br.is_end():
            flags = br.read_byte()
            player = {}

            if flags & 1 == 1:
                player["name"] = br.read_pascal_string()

            if flags & 2 == 2:
                player["team"] = br.read_pascal_string()

            if flags & 4 == 4:
                player["skin"] = br.read_pascal_string()

            if flags & 8 == 8:
                try:
                    player["score"] = int(br.read_pascal_string())
                except ValueError:
                    player["score"] = 0

            if flags & 16 == 16:
                try:
                    player["ping"] = int(br.read_pascal_string())
                except ValueError:
                    player["ping"] = 0

            if flags & 32 == 32:
                try:
                    player["time"] = int(br.read_pascal_string())
                except ValueError:
                    player["time"] = 0

            players.append(Player(**player))

        return players


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # mtasa
        ase = ASE(host="79.137.97.3", port=22126, timeout=10.0)
        status = await ase.get_status()
        print(status)

    asyncio.run(main_async())
