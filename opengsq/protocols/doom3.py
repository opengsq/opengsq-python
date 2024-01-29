from __future__ import annotations

import re
from typing import Union

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.doom3 import Status


class Doom3(ProtocolBase):
    """
    This class represents the Doom3 Protocol. It provides methods to interact with the Doom3 API.
    """

    full_name = "Doom3 Protocol"

    _player_fields = {
        "doom": ["id", "ping", "rate", "name"],
        "quake4": ["id", "ping", "rate", "name", "clantag"],
        "etqw": ["id", "ping", "name", "clantag_pos", "clantag", "typeflag"],
    }

    async def get_status(self, strip_color=True) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :param strip_color: A boolean indicating whether to strip color codes from the player names.
        :return: A Status object containing the server information and player list.

        This function sends a request to the game server and processes the response to extract server information and player details. If the 'strip_color' parameter is set to True, color codes in player names are removed. The function returns a Status object which includes a dictionary of server information and a list of players.
        """
        request = b"\xFF\xFFgetInfo\x00ogsq\x00"
        response = await UdpClient.communicate(self, request)

        # Remove the first two 0xFF
        br = BinaryReader(response[2:])
        header = br.read_string()

        if header != "infoResponse":
            raise InvalidPacketException(
                f"Packet header mismatch. Received: {header}. Expected: infoResponse."
            )

        # Read challenge
        br.read_bytes(4)

        if br.read_bytes(4) != b"\xff\xff\xff\xff":
            br.stream_position -= 4

        info = {}

        # Read protocol version
        minor = br.read_short()
        major = br.read_short()
        info["version"] = f"{major}.{minor}"

        # Read packet size
        if br.read_long() != br.remaining_bytes():
            br.stream_position -= 4

        # Key / value pairs, delimited by an empty pair
        while br.remaining_bytes() > 0:
            key = br.read_string().strip()
            val = br.read_string().strip()

            if key == "" and val == "":
                break

            info[key] = Doom3.strip_colors(val) if strip_color else val

        players = []

        stream_position = br.stream_position

        # Try parse the fields
        for mod in self._player_fields.keys():
            try:
                players = self.__parse_player(br, self._player_fields[mod], strip_color)
                break
            except Exception:
                players = []
                br.stream_position = stream_position

        status = Status(info, players)

        return status

    def __parse_player(
        self, br: BinaryReader, fields: list, strip_color: bool
    ) -> list[dict[str, Union[int, str]]]:
        """
        Parses the player information from the BinaryReader object.

        :param br: The BinaryReader object containing the player information.
        :param fields: A list of fields to parse from the BinaryReader object.
        :param strip_color: A boolean indicating whether to strip color codes from the player information.
        :return: A list of dictionaries containing the player information.
        """
        players = []

        def value_by_field(field: str, br: BinaryReader):
            if field == "id" or field == "clantag_pos" or field == "typeflag":
                return br.read_byte()
            elif field == "ping":
                return br.read_short()
            elif field == "rate":
                return br.read_long()

            string = br.read_string()

            return Doom3.strip_colors(string) if strip_color else string

        while True:
            player = {field: value_by_field(field, br) for field in fields}

            if player["id"] == 32:
                break

            players.append(player)

        return players

    @staticmethod
    def strip_colors(text: str) -> str:
        """
        Strips color codes from the given text.

        :param text: The text to strip color codes from.
        :return: The text with color codes stripped.
        """
        return re.compile("\\^(X.{6}|.)").sub("", text)


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # doom3
        doom3 = Doom3(host="66.85.14.240", port=27666, timeout=5.0)
        info = await doom3.get_status()
        print(info)

        # etqw
        doom3 = Doom3(host="178.162.135.83", port=27735, timeout=5.0)
        info = await doom3.get_status()
        print(info)

        # quake4
        doom3 = Doom3(host="88.99.0.7", port=28007, timeout=5.0)
        info = await doom3.get_status()
        print(info)

    asyncio.run(main_async())
