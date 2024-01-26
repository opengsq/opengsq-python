from __future__ import annotations

import re

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

    async def get_details(self) -> Status:
        """
        Asynchronously gets the details of a server.

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
            server_name=self._read_string(br),
            map_name=self._read_string(br),
            game_type=self._read_string(br),
            num_players=br.read_long(),
            max_players=br.read_long(),
            ping=br.read_long(),
            flags=br.read_long(),
            skill=self._read_string(br),
        )

    async def get_rules(self) -> dict:
        """
        Asynchronously gets the rules of a server.

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
            key = self._read_string(br)
            val = self._read_string(br)

            if key.lower() == "mutator":
                rules["Mutators"].append(val)
            else:
                rules[key] = val

        return rules

    async def get_players(self) -> list[Player]:
        """
        Asynchronously gets the players of a server.

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
                name=self._read_string(br),
                ping=br.read_long(),
                score=br.read_long(),
                stats_id=br.read_long(),
            )
            players.append(player)

        return players

    @staticmethod
    def strip_colors(text: str):
        """
        Strips color codes from a string.

        Args:
            text (str): The string to strip color codes from.

        Returns:
            str: The string with color codes stripped.
        """
        return re.compile("\x1b...|[\x00-\x1a]").sub("", text)

    def _read_string(self, br: BinaryReader):
        """
        Reads a string from a BinaryReader object.

        Args:
            br (BinaryReader): The BinaryReader object to read the string from.

        Returns:
            str: The string read from the BinaryReader object.
        """
        length = br.read_byte()
        encoding = "utf-8"

        if length >= 128:
            length = (length & 0x7F) * 2
            encoding = "utf-16"

        return Unreal2.strip_colors(br.read_bytes(length).decode(encoding, "ignore"))


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # ut2004
        unreal2 = Unreal2(host="109.230.224.189", port=6970)
        details = await unreal2.get_details()
        print(details)
        rules = await unreal2.get_rules()
        print(rules)
        players = await unreal2.get_players()
        print(players)

    asyncio.run(main_async())
