from __future__ import annotations

import json
import re
import struct
from typing import Any

from opengsq.responses.minecraft import StatusPre17
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import TcpClient


class Minecraft(ProtocolBase):
    """
    This class represents the Minecraft Protocol. It provides methods to interact with the Minecraft API. (https://wiki.vg/Server_List_Ping)
    """

    full_name = "Minecraft Protocol"

    async def get_status(self, version=47, strip_color=True) -> dict[str, Any]:
        """
        Asynchronously retrieves the status of the game server.

        :param version: The protocol version number. Defaults to 47.
        :param strip_color: Whether to strip color from the response. Defaults to True.
        :return: A dictionary containing the status of the game server.
        """
        # Prepare the request
        address = self._host.encode("utf8")
        protocol = self._pack_varint(version)
        request = (
            b"\x00"
            + protocol
            + self._pack_varint(len(address))
            + address
            + struct.pack("H", self._port)
            + b"\x01"
        )
        request = self._pack_varint(len(request)) + request + b"\x01\x00"

        with TcpClient() as tcpClient:
            tcpClient.settimeout(self._timeout)
            await tcpClient.connect((self._host, self._port))
            tcpClient.send(request)

            response = await tcpClient.recv()
            br = BinaryReader(response)
            length = self._unpack_varint(br)

            # Keep recv() until reach packet length
            while len(response) < length:
                response += await tcpClient.recv()

        # Read fill response
        br = BinaryReader(response)
        self._unpack_varint(br)  # packet length
        self._unpack_varint(br)  # packet id
        count = self._unpack_varint(br)  # json length

        # The packet may response with two json objects, so we need to get the json length exactly
        data = json.loads(br.read_bytes(count).decode("utf-8"))

        if strip_color:
            if "sample" in data["players"]:
                for i, player in enumerate(data["players"]["sample"]):
                    data["players"]["sample"][i]["name"] = Minecraft.strip_colors(
                        player["name"]
                    )

            if isinstance(data["description"], str):
                data["description"] = Minecraft.strip_colors(data["description"])

            if "text" in data["description"] and isinstance(
                data["description"]["text"], str
            ):
                data["description"]["text"] = Minecraft.strip_colors(
                    data["description"]["text"]
                )

            if "extra" in data["description"] and isinstance(
                data["description"]["extra"], list
            ):
                for i, extra in enumerate(data["description"]["extra"]):
                    if isinstance(extra["text"], str):
                        data["description"]["extra"][i][
                            "text"
                        ] = Minecraft.strip_colors(extra["text"])

        return data

    async def get_status_pre17(self, strip_color=True) -> StatusPre17:
        """
        Asynchronously retrieves the status of a game server that uses a version older than Minecraft 1.7.

        :param strip_color: Whether to strip color from the response. Defaults to True.
        :return: A StatusPre17 object containing the status of the game server.
        """
        response = await TcpClient.communicate(self, b"\xFE\x01")

        br = BinaryReader(response)
        header = br.read_byte()

        if header != 0xFF:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(0xFF)
                )
            )

        br.read_bytes(2)  # length of the following string
        items = br.read().split(b"\x00\x00")

        result = {}
        result["protocol"] = str(items[1], "utf-16be")
        result["version"] = str(items[2], "utf-16be")
        result["motd"] = str(items[3], "utf-16be")
        result["num_players"] = int(str(items[4], "utf-16be"))
        result["max_players"] = int(str(items[5], "utf-16be"))

        if strip_color:
            result["motd"] = Minecraft.strip_colors(result["motd"])

        return StatusPre17(**result)

    @staticmethod
    def strip_colors(text: str) -> get_status_pre17:
        """
        Strips color codes from the given text.

        :param text: The text to strip color codes from.
        :return: The text with color codes stripped.
        """
        return re.compile(r"\u00A7[0-9A-FK-OR]", re.IGNORECASE).sub("", text)

    def _pack_varint(self, val: int):
        total = b""

        if val < 0:
            val = (1 << 32) + val

        while val >= 0x80:
            bits = val & 0x7F
            val >>= 7
            total += struct.pack("B", (0x80 | bits))

        bits = val & 0x7F
        total += struct.pack("B", bits)

        return total

    def _unpack_varint(self, br: BinaryReader):
        total = 0
        shift = 0
        val = 0x80

        while val & 0x80:
            val = struct.unpack("B", br.read_bytes(1))[0]
            total |= (val & 0x7F) << shift
            shift += 7

        if total & (1 << 31):
            total -= 1 << 32

        return total


if __name__ == "__main__":
    import asyncio

    async def main_async():
        minecraft = Minecraft(host="mc.goldcraft.ir", port=25565, timeout=5.0)
        status = await minecraft.get_status(47, strip_color=True)
        print(status)
        status_pre17 = await minecraft.get_status_pre17()
        print(status_pre17)

    asyncio.run(main_async())
