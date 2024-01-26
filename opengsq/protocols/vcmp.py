from __future__ import annotations

import struct
from opengsq.responses.vcmp import Player, Status

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import Socket, UdpClient


class Vcmp(ProtocolBase):
    """
    This class represents the Vice City Multiplayer Protocol. It provides methods to interact with the Vice City Multiplayer API.
    """

    full_name = "Vice City Multiplayer Protocol"

    _request_header = b"VCMP"
    _response_header = b"MP04"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        response = await self.__send_and_receive(b"i")

        br = BinaryReader(response)

        return Status(
            version=str(
                br.read_bytes(12).strip(b"\x00"), encoding="utf-8", errors="ignore"
            ),
            password=br.read_byte(),
            num_players=br.read_short(),
            max_players=br.read_short(),
            server_name=self.__read_string(br, 4),
            game_type=self.__read_string(br, 4),
            language=self.__read_string(br, 4),
        )

    async def get_players(self) -> list[Player]:
        """
        Asynchronously retrieves the list of players on the game server.

        :return: A list of Player objects representing the players on the game server.
        """
        """Server may not response when numplayers > 100"""
        response = await self.__send_and_receive(b"c")

        br = BinaryReader(response)
        numplayers = br.read_short()
        players = [Player(self.__read_string(br)) for _ in range(numplayers)]

        return players

    async def __send_and_receive(self, data: bytes):
        """
        Asynchronously sends the given data to the game server and receives the response.

        :param data: The data to send to the game server.
        :return: The response from the game server.
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

        return response[len(self._response_header) + len(packet_header) :]

    def __read_string(self, br: BinaryReader, read_offset=1):
        """
        Reads a string from the given BinaryReader object.

        :param br: The BinaryReader object to read the string from.
        :param read_offset: The offset to start reading from.
        :return: The string read from the BinaryReader object.
        """
        length = br.read_byte() if read_offset == 1 else br.read_long()
        return str(br.read_bytes(length), encoding="utf-8", errors="ignore")


if __name__ == "__main__":
    import asyncio

    async def main_async():
        vcmp = Vcmp(host="51.178.65.136", port=8114, timeout=5.0)
        status = await vcmp.get_status()
        print(status)
        players = await vcmp.get_players()
        print(players)

    asyncio.run(main_async())
