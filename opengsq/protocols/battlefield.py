from __future__ import annotations

from opengsq.responses.battlefield import Info, VersionInfo
from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import TcpClient


class Battlefield(ProtocolBase):
    """
    This class represents the Battlefield Protocol. It provides methods to interact with the Battlefield API.
    """

    full_name = "Battlefield Protocol"

    _info = b"\x00\x00\x00\x21\x1b\x00\x00\x00\x01\x00\x00\x00\x0a\x00\x00\x00serverInfo\x00"
    _version = (
        b"\x00\x00\x00\x22\x18\x00\x00\x00\x01\x00\x00\x00\x07\x00\x00\x00version\x00"
    )
    _players = b"\x00\x00\x00\x23\x24\x00\x00\x00\x02\x00\x00\x00\x0b\x00\x00\x00listPlayers\x00\x03\x00\x00\x00all\x00"

    async def get_info(self) -> Info:
        """
        Asynchronously retrieves the information of the game server.

        :return: An Info object containing the information of the game server.
        """
        data = await self.__get_data(self._info)

        info = {}
        info["hostname"] = str(data.pop(0)).strip()
        info["num_players"] = int(data.pop(0))
        info["max_players"] = int(data.pop(0))
        info["game_type"] = data.pop(0)
        info["map"] = data.pop(0)
        info["rounds_played"] = int(data.pop(0))
        info["rounds_total"] = int(data.pop(0))
        num_teams = int(data.pop(0))
        info["teams"] = [float(data.pop(0)) for _ in range(num_teams)]
        info["target_score"] = int(data.pop(0))
        info["status"] = data.pop(0)
        info["ranked"] = data.pop(0) == "true"
        info["punk_buster"] = data.pop(0) == "true"
        info["password"] = data.pop(0) == "true"
        info["uptime"] = int(data.pop(0))
        info["round_time"] = int(data.pop(0))

        try:
            if data[0] == "BC2":
                info["mod"] = data.pop(0)
                data.pop(0)

            info["ip_port"] = data.pop(0)
            info["punk_buster_version"] = data.pop(0)
            info["join_queue"] = data.pop(0) == "true"
            info["region"] = data.pop(0)
            info["ping_site"] = data.pop(0)
            info["country"] = data.pop(0)

            try:
                info["blaze_player_count"] = int(data[0])
                info["blaze_game_state"] = data[1]
            except Exception:
                info["quick_match"] = data.pop(0) == "true"
        except Exception:
            pass

        return Info(**info)

    async def get_version(self) -> VersionInfo:
        """
        Asynchronously retrieves the version information of the game server.

        :return: A VersionInfo object containing the version information of the game server.
        """
        data = await self.__get_data(self._version)
        return VersionInfo(data[0], data[1])

    async def get_players(self) -> list[dict[str, str]]:
        """
        Asynchronously retrieves the list of players on the game server.

        :return: A list of dictionaries containing the player information.
        """
        data = await self.__get_data(self._players)
        count = int(data.pop(0))  # field count
        fields, data = data[:count], data[count:]
        numplayers = int(data.pop(0))
        players = []

        for _ in range(numplayers):
            values, data = data[:count], data[count:]
            players.append(dict(zip(fields, values)))

        return players

    async def __get_data(self, request: bytes):
        """
        Asynchronously sends the given request to the game server and receives the response.

        :param request: The request to send to the game server.
        :return: A list containing the response data from the game server.
        """
        response = await TcpClient.communicate(self, request)
        return self.__decode(response)

    def __decode(self, response: bytes):
        """
        Decodes the given response from the game server.

        :param response: The response to decode.
        :return: A list containing the decoded response data.
        """
        br = BinaryReader(response)
        br.read_long()  # header
        br.read_long()  # packet length
        count = br.read_long()  # string count
        data = []

        for _ in range(count):
            br.read_long()  # length of the string
            data.append(br.read_string())

        return data[1:]


if __name__ == "__main__":
    import asyncio

    async def main_async():
        entries = [
            ("91.206.15.69", 48888),  # bfbc2
            ("94.250.199.214", 47200),  # bf3
            ("74.91.124.140", 47200),  # bf4
            ("185.189.255.240", 47600),  # bfh
        ]

        for address, query_port in entries:
            battlefield = Battlefield(address, query_port, timeout=10.0)
            info = await battlefield.get_info()
            print(info)
            version = await battlefield.get_version()
            print(version)
            players = await battlefield.get_players()
            print(players)

    asyncio.run(main_async())
