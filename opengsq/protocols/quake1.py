from __future__ import annotations

import re

from opengsq.responses.quake1 import Player, Status
from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Quake1(ProtocolBase):
    """
    This class represents the Quake1 Protocol. It provides methods to interact with the Quake1 API.
    """

    full_name = "Quake1 Protocol"

    def __init__(self, host: str, port: int, timeout: float = 5.0):
        """
        Initializes the Quake1 Query Protocol.

        :param host: The host of the game server.
        :param port: The port of the game server.
        :param timeout: The timeout for the connection. Defaults to 5.0.
        """
        super().__init__(host, port, timeout)
        self._delimiter1 = b"\\"
        self._delimiter2 = b"\n"
        self._request_header = b"status"
        self._response_header = "n"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        br = await self._get_response_binary_reader()

        return Status(info=self._parse_info(br), players=self._parse_players(br))

    async def _get_response_binary_reader(self) -> BinaryReader:
        """
        Asynchronously gets the response from the game server and returns a BinaryReader object.

        :return: A BinaryReader object containing the response from the game server.
        """
        response_data = await self._connect_and_send(self._request_header)

        br = BinaryReader(response_data)
        header = br.read_string(self._delimiter1)

        if header != self._response_header:
            raise Exception(
                f"Packet header mismatch. Received: {header}. Expected: {self._response_header}."
            )

        return br

    def _parse_info(self, br: BinaryReader) -> dict:
        """
        Parses the information from the given BinaryReader object.

        :param br: The BinaryReader object to parse the information from.
        :return: A dictionary containing the information.
        """
        info = {}

        # Read all key values until meet \n
        while br.remaining_bytes() > 0:
            key = br.read_string(self._delimiter1)

            if key == "":
                break

            info[key] = br.read_string([self._delimiter1, self._delimiter2])

            br.stream_position -= 1

            if bytes([br.read_byte()]) == self._delimiter2:
                break

        return info

    def _parse_players(self, br: BinaryReader) -> list:
        """
        Parses the players from the given BinaryReader object.

        :param br: The BinaryReader object to parse the players from.
        :return: A list containing the players.
        """
        players = []

        for matches in self._get_player_match_collections(br):
            matches: list[re.Match] = [match.group() for match in matches]

            players.append(
                Player(
                    id=int(matches[0]),
                    score=int(matches[1]),
                    time=int(matches[2]),
                    ping=int(matches[3]),
                    name=str(matches[4]).strip('"'),
                    skin=str(matches[5]).strip('"'),
                    color1=int(matches[6]),
                    color2=int(matches[7]),
                )
            )

        return players

    def _get_player_match_collections(self, br: BinaryReader):
        """
        Gets the player match collections from the given BinaryReader object.

        :param br: The BinaryReader object to get the player match collections from.
        :return: The player match collections.
        """
        match_collections = []

        # Regex to split with whitespace and double quote
        regex = re.compile(r'"(\\"|[^"])*?"|[^\s]+')

        # Read all players
        while br.remaining_bytes() > 1:
            match_collections.append(regex.finditer(br.read_string(self._delimiter2)))

        return match_collections

    async def _connect_and_send(self, data):
        """
        Asynchronously connects to the game server and sends the given data.

        :param data: The data to send to the game server.
        :return: The response from the game server.
        """
        header = b"\xFF\xFF\xFF\xFF"
        response_data = await UdpClient.communicate(self, header + data + b"\x00")

        # Remove the last 0x00 if exists (Only if Quake1)
        if response_data[-1] == 0:
            response_data = response_data[:-1]

        # Add \n at the last of responseData if not exists
        if response_data[-1] != self._delimiter2:
            response_data += self._delimiter2

        # Remove the first four 0xFF
        return response_data[len(header) :]


if __name__ == "__main__":
    import asyncio

    async def main_async():
        quake1 = Quake1(host="35.185.44.174", port=27500, timeout=5.0)
        status = await quake1.get_status()
        print(status)

    asyncio.run(main_async())
