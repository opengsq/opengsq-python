from __future__ import annotations

import re

from opengsq.responses.quake2 import Status
from opengsq.binary_reader import BinaryReader
from opengsq.protocols.quake2 import Quake2
from opengsq.exceptions import InvalidPacketException


class Quake3(Quake2):
    """
    This class represents the Quake3 Protocol. It provides methods to interact with the Quake3 API.
    """

    full_name = "Quake3 Protocol"

    def __init__(self, host: str, port: int, timeout: float = 5.0):
        """
        Initializes the Quake3 object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param timeout: The timeout for the server connection.
        """
        super().__init__(host, port, timeout)
        self._request_header = b"getstatus"
        self._response_header = "statusResponse\n"

    async def get_info(self, strip_color=True) -> dict[str, str]:
        """
        Asynchronously retrieves the information of the game server.

        :param strip_color: A boolean indicating whether to strip color codes from the information.
        :return: A dictionary containing the information of the game server.
        """
        response_data = await self._connect_and_send(b"getinfo opengsq")

        br = BinaryReader(response_data)
        header = br.read_string(self._delimiter1)
        response_header = "infoResponse\n"

        if header != response_header:
            raise InvalidPacketException(
                f"Packet header mismatch. Received: {header}. Expected: {response_header}."
            )

        info = self._parse_info(br)

        if not strip_color:
            return info

        if "hostname" in info:
            info["hostname"] = Quake3.strip_colors(info["hostname"])

        return info

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
        quake3 = Quake3(host="108.61.18.110", port=27960, timeout=5.0)
        info = await quake3.get_info()
        print(info)
        status = await quake3.get_status()
        print(status)

    asyncio.run(main_async())
