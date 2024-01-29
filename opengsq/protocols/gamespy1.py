from __future__ import annotations

import re

from opengsq.responses.gamespy1 import Status
from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class GameSpy1(ProtocolBase):
    """GameSpy Protocol version 1"""

    full_name = "GameSpy Protocol version 1"

    # Legacy:UT_Server_Query - (https://wiki.beyondunreal.com/Legacy:UT_Server_Query)
    # Query_commands - (https://wiki.beyondunreal.com/XServerQuery#Query_commands)
    class __Request:
        BASIC = b"\\basic\\"
        INFO = b"\\info\\xserverquery"
        RULES = b"\\rules\\xserverquery"
        PLAYERS = b"\\players\\xserverquery"
        STATUS = b"\\status\\xserverquery"
        TEAMS = b"\\teams\\"

    async def get_basic(self) -> dict[str, str]:
        """
        Asynchronously retrieves the basic information of the game server.

        :return: A dictionary containing the basic information of the game server.
        """
        return self.__parse_as_key_values(
            await self.__connect_and_send(self.__Request.BASIC)
        )

    # Server may still response with Legacy version
    async def get_info(self, xserverquery: bool = True) -> dict[str, str]:
        """
        Asynchronously retrieves the information of the current game running on the server.

        :param xserverquery: A boolean indicating whether to use XServerQuery.
        :return: A dictionary containing the information of the current game.
        """
        data = (
            xserverquery
            and self.__Request.INFO
            or self.__Request.INFO.replace(b"xserverquery", b"")
        )
        return self.__parse_as_key_values(await self.__connect_and_send(data))

    async def get_rules(self, xserverquery: bool = True) -> dict[str, str]:
        """
        Asynchronously retrieves the rules of the current game running on the server.

        :param xserverquery: A boolean indicating whether to use XServerQuery.
        :return: A dictionary containing the rules of the current game.
        """
        data = (
            xserverquery
            and self.__Request.RULES
            or self.__Request.RULES.replace(b"xserverquery", b"")
        )
        return self.__parse_as_key_values(await self.__connect_and_send(data))

    async def get_players(self, xserverquery: bool = True) -> list[dict[str, str]]:
        """
        Asynchronously retrieves the information of each player on the server.

        :param xserverquery: A boolean indicating whether to use XServerQuery.
        :return: A list containing the information of each player.
        """
        data = (
            xserverquery
            and self.__Request.PLAYERS
            or self.__Request.PLAYERS.replace(b"xserverquery", b"")
        )
        return self.__parse_as_object(await self.__connect_and_send(data))

    async def get_status(self, xserverquery: bool = True) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        XServerQuery: \\info\\xserverquery\\rules\\xserverquery\\players\\xserverquery
        Old response: \\basic\\info\\rules\\players\\

        If the server uses XServerQuery, he sends you the new information, otherwise he'll give you back the old information.

        :param xserverquery: A boolean indicating whether to use XServerQuery.
        :return: A Status object containing the status of the game server.
        """
        data = (
            xserverquery
            and self.__Request.STATUS
            or self.__Request.STATUS.replace(b"xserverquery", b"")
        )
        br = await self.__connect_and_send(data)

        info = self.__parse_as_key_values(br, is_status=True)
        players = self.__parse_as_object(br, is_player=True)
        teams = [] if br.is_end() else self.__parse_as_object(br)

        return Status(info, players, teams)

    async def get_teams(self) -> list[dict[str, str]]:
        """
        Asynchronously retrieves the information of each team on the server.

        :return: A list containing the information of each team.
        """
        return self.__parse_as_object(
            await self.__connect_and_send(self.__Request.TEAMS)
        )

    # Receive packets and sort it
    async def __get_packets_response(self, udpClient: UdpClient):
        payloads = {}
        packet_count = -1

        # Loop until received all packets
        while packet_count == -1 or len(payloads) < packet_count:
            packet = await udpClient.recv()

            # Get the packet number from query_id
            r = re.compile(rb"\\queryid\\\d+\.(\d+)")
            number, payload = int(r.search(packet).group(1)), r.sub(b"", packet)

            # If it is the last packet, it will contain b'\\final\\' at the end of the response
            if payload.endswith(b"\\final\\"):
                # Save the packet count
                packet_count = number

                # Remove the last b'\\final\\'
                payload = payload[:-7]

            # Save the payload, remove the first byte if it is the first packet
            payloads[number] = payload[1:] if number == 1 else payload

        # Sort the payload and return as bytes
        response = b"".join(payloads[number] for number in sorted(payloads))

        return response

    async def __connect_and_send(self, data) -> BinaryReader:
        # Connect to remote host
        with UdpClient() as udpClient:
            udpClient.settimeout(self._timeout)
            await udpClient.connect((self._host, self._port))

            udpClient.send(data)
            br = BinaryReader(await self.__get_packets_response(udpClient))

        return br

    def __parse_as_key_values(
        self, br: BinaryReader, is_status=False
    ) -> dict[str, str]:
        kv = {}

        # Bind key value
        while br.remaining_bytes() > 0:
            key = br.read_string(b"\\").lower()

            # Check is the end of key_values
            if is_status:
                items = key.split("_")

                if len(items) > 1 and items[1].isdigit():
                    # Read already, so add it back
                    br.prepend_bytes(key.encode() + b"\\")
                    break

            value = br.read_string(b"\\")
            kv[key] = value.strip()

        return kv

    def __parse_as_object(
        self, br: BinaryReader, is_player=False
    ) -> list[dict[str, str]]:
        items, keyhashes, filters = {}, [], []

        while br.remaining_bytes() > 0:
            # Get the key, for example player_1, frags_1, ping_1, etc...
            key = br.read_string(b"\\").lower()

            if is_player and key.startswith("teamname_"):
                # Read already, so add it back
                br.prepend_bytes(key.encode() + b"\\")
                break

            # Extract to name and index, for example name=player, index=1
            matches = re.search(r"(.+?)_(\d+)", key)
            name = matches.group(1)
            name = "player" if name == "playername" else name
            name = "team" if name == "teamname" else name
            index = int(matches.group(2))

            # Get the value, and strip it since some values contain whitespaces
            value = br.read_string(b"\\").strip()

            # Some servers (bf1942) report the same player multiple times, so filter it by keyhash
            if name == "keyhash":
                if value in keyhashes:
                    filters.append(index)
                else:
                    keyhashes.append(value)

            # Create a dict on items if next index appears
            if index not in items:
                items[index] = {}

            # Save
            items[index][name] = value

        # Filter items by filters
        return [v for k, v in items.items() if k not in filters]


if __name__ == "__main__":
    import asyncio

    async def main_async():
        gs1 = GameSpy1(host="51.81.48.224", port=23000, timeout=5.0)  # bfield1942
        # gs1 = GameSpy1(address='139.162.235.20', query_port=7778, timeout=5.0)  # ut
        # gs1 = GameSpy1(address='192.223.24.6', query_port=7778, timeout=5.0)  # ut
        gs1 = GameSpy1(host="141.94.205.35", port=12300, timeout=5.0)  # mohaa
        status = await gs1.get_status()
        print(status)

    asyncio.run(main_async())
