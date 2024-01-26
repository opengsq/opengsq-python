from __future__ import annotations

import struct

from opengsq.responses.samp import Player, Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import Socket, UdpClient


class Samp(ProtocolBase):
    """
    This class represents the San Andreas Multiplayer Protocol. It provides methods to interact with the San Andreas Multiplayer API.
    """

    full_name = "San Andreas Multiplayer Protocol"

    _request_header = b"SAMP"
    _response_header = b"SAMP"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        br = await self.__send_and_receive(b"i")

        return Status(
            password=br.read_byte() != 0,
            num_players=br.read_short(),
            max_players=br.read_short(),
            server_name=self.__read_string(br, 4),
            game_type=self.__read_string(br, 4),
            language=self.__read_string(br, 4),
        )

    async def get_players(self) -> list[Player]:
        """
        Asynchronously retrieves the players of the game server. The server may not respond when the number of players is greater than 100.

        :return: A list containing the players of the game server.
        """
        br = await self.__send_and_receive(b"d")
        numplayers = br.read_short()
        players = [
            Player(
                id=br.read_byte(),
                name=self.__read_string(br),
                score=br.read_long(),
                ping=br.read_long(),
            )
            for _ in range(numplayers)
        ]
        return players

    async def get_rules(self) -> dict[str, str]:
        """
        Asynchronously retrieves the rules of the game server.

        :return: A dictionary containing the rules of the game server.
        """
        br = await self.__send_and_receive(b"r")
        numrules = br.read_short()

        return dict(
            (self.__read_string(br), self.__read_string(br)) for _ in range(numrules)
        )

    async def __send_and_receive(self, data: bytes):
        """
        Asynchronously sends the given data to the game server and receives the response.

        :param data: The data to send to the game server.
        :return: A BinaryReader object containing the response from the game server.
        """
        # Format the address
        host = await Socket.gethostbyname(self._host)
        packet_header = (
            struct.pack("BBBBH", *map(int, host.split(".") + [self._port])) + data
        )
        request = self._request_header + packet_header

        # Validate the response
        response = await UdpClient.communicate(self, request)
        header = response[: len(self._response_header)]

        if header != self._response_header:
            raise InvalidPacketException(
                f"Packet header mismatch. Received: {header}. Expected: {self._response_header}."
            )

        return BinaryReader(response[len(self._response_header) + len(packet_header) :])

    def __read_string(self, br: BinaryReader, read_offset=1):
        """
        Reads a string from the given BinaryReader object.

        :param br: The BinaryReader object to read the string from.
        :param read_offset: The read offset. Defaults to 1.
        :return: The string read from the BinaryReader object.
        """
        length = br.read_byte() if read_offset == 1 else br.read_long()
        return str(br.read_bytes(length), encoding="utf-8", errors="ignore")


if __name__ == "__main__":
    import asyncio

    async def main_async():
        samp = Samp(host="51.254.178.238", port=7777, timeout=5.0)
        status = await samp.get_status()
        print(status)

        await asyncio.sleep(5)
        players = await samp.get_players()
        print(players)

        await asyncio.sleep(5)
        rules = await samp.get_rules()
        print(rules)

    asyncio.run(main_async())
