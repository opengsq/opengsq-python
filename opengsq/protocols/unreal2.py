from __future__ import annotations

import re
from typing import Any

from opengsq.responses.unreal2 import Player, Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Unreal2(ProtocolBase):
    """
    The Unreal2 class inherits from the ProtocolBase class and represents the Unreal 2 Protocol.
    It provides methods to get details, rules, and players from a server using the Unreal 2 Protocol.
    """

    full_name = "Unreal 2 Protocol"

    _DETAILS = 0x00
    _RULES = 0x01
    _PLAYERS = 0x02

    async def get_details(self, strip_color=True) -> Status:
        """
        Asynchronously gets the details of a server.

        Args:
            strip_color (bool, optional): If True, strips color codes from the server name. Defaults to True.

        Returns:
            Status: A Status object containing the details of the server.
        """
        response = await UdpClient.communicate(
            self, b"\x79\x00\x00\x00" + bytes([self._DETAILS])
        )

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._DETAILS:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(self._DETAILS)
                )
            )

        return Status(
            server_id=br.read_long(),
            server_ip=br.read_string(),
            game_port=br.read_long(),
            query_port=br.read_long(),
            server_name=self._read_string(br, strip_color, False),
            map_name=self._read_string(br, strip_color),
            game_type=self._read_string(br, strip_color),
            num_players=br.read_long(),
            max_players=br.read_long(),
            ping=br.read_long(),
            flags=br.read_long(),
            skill=self._read_string(br, strip_color),
        )

    async def get_rules(self, strip_color=True) -> dict[str, Any]:
        """
        Asynchronously gets the rules of a server.

        Args:
            strip_color (bool, optional): If True, strips color codes. Defaults to True.

        Returns:
            dict: A dictionary containing the rules of the server.
        """
        response = await UdpClient.communicate(
            self, b"\x79\x00\x00\x00" + bytes([self._RULES])
        )

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._RULES:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(self._RULES)
                )
            )

        rules = {}
        rules["Mutators"] = []

        while not br.is_end():
            key = self._read_string(br, strip_color)
            val = self._read_string(br, strip_color)

            if key.lower() == "mutator":
                rules["Mutators"].append(val)
            elif key:
                rules[key] = val

        return rules

    async def get_players(self, strip_color=True) -> list[Player]:
        """
        Asynchronously gets the players of a server.

        Args:
            strip_color (bool, optional): If True, strips color codes. Defaults to True.

        Returns:
            list: A list of Player objects representing the players of the server.
        """
        response = await UdpClient.communicate(
            self, b"\x79\x00\x00\x00" + bytes([self._PLAYERS])
        )

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._PLAYERS:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(self._PLAYERS)
                )
            )

        players = []

        while not br.is_end():
            player = Player(
                id=br.read_long(),
                name=self._read_string(br, strip_color),
                ping=br.read_long(),
                score=br.read_long(),
                stats_id=br.read_long(),
            )
            players.append(player)

        return players

    @staticmethod
    def strip_color(text: bytes) -> bytes:
        """
        Strips color codes from a string.

        Args:
            text (str): The string to strip color codes from.

        Returns:
            str: The string with color codes stripped.
        """
        return re.compile(b"\x1b...|[\x00-\x1a]").sub(b"", text)

    def _read_string(self, br: BinaryReader, strip_color: bool, pascal=True):
        """
        Reads a string from a BinaryReader object.

        Args:
            br (BinaryReader): The BinaryReader object to read the string from.

        Returns:
            str: The string read from the BinaryReader object.
        """
        length = br.read_byte()

        if pascal:
            if length >= 128:
                length = (length & 0x7F) * 2

            bytes_string = br.read_bytes(length)
        else:
            bytes_string = b""

            while br.remaining_bytes() > 0:
                stream_byte = bytes([br.read_byte()])

                if stream_byte == b"\0":
                    break

                bytes_string += stream_byte

        if strip_color:
            bytes_string = Unreal2.strip_color(bytes_string)

        string = bytes_string.decode("utf-8", "ignore").strip()

        return string


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # ut2004
        # unreal2 = Unreal2(host="109.230.224.189", port=6970)
        # unreal2 = Unreal2(host="185.80.128.168", port=7708)
        unreal2 = Unreal2(host="45.235.99.76", port=7710)
        # unreal2 = Unreal2(host="51.195.117.236", port=9981)
        unreal2 = Unreal2(host="80.4.151.145", port=7778)
        # details = await unreal2.get_details()
        # print(details)
        rules = await unreal2.get_rules()
        print(rules)
        # players = await unreal2.get_players()
        # print(players)

    asyncio.run(main_async())
