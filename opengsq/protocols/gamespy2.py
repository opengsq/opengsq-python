from enum import Flag, auto

from opengsq.responses.gamespy2 import Status
from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class GameSpy2(ProtocolBase):
    """
    This class represents the GameSpy Protocol version 2. It provides methods to interact with the GameSpy API.
    """

    full_name = "GameSpy Protocol version 2"

    class Request(Flag):
        INFO = auto()
        PLAYERS = auto()
        TEAMS = auto()

    async def get_status(
        self, request: Request = Request.INFO | Request.PLAYERS | Request.TEAMS
    ) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :param request: A Request object indicating the type of information to retrieve.
        :return: A Status object containing the status of the game server.
        """
        data = b"\xFE\xFD\x00\x04\x05\x06\x07" + self.__get_request_bytes(request)
        response = await UdpClient.communicate(self, data)

        # Remove the first 5 bytes { 0x00, 0x04, 0x05, 0x06, 0x07 }
        br = BinaryReader(response[5:])

        info = (
            self.__get_info(br) if self.__has_flag(request, self.Request.INFO) else {}
        )
        players = (
            self.__get_players(br)
            if self.__has_flag(request, self.Request.PLAYERS)
            else []
        )
        teams = (
            self.__get_teams(br) if self.__has_flag(request, self.Request.TEAMS) else []
        )

        return Status(info, players, teams)

    def __get_request_bytes(self, request: Request):
        """
        Gets the request bytes for the given request.

        :param request: The request to get the request bytes for.
        :return: The request bytes.
        """
        request_bytes = (
            self.__has_flag(request, self.Request.INFO) and b"\xFF" or b"\x00"
        )
        request_bytes += (
            self.__has_flag(request, self.Request.PLAYERS) and b"\xFF" or b"\x00"
        )
        request_bytes += (
            self.__has_flag(request, self.Request.TEAMS) and b"\xFF" or b"\x00"
        )

        return request_bytes

    def __has_flag(self, request, flag) -> bool:
        """
        Checks if the given request has the specified flag.

        :param request: The request to check.
        :param flag: The flag to check for.
        :return: True if the request has the flag, False otherwise.
        """
        return request & flag == flag

    def __get_info(self, br: BinaryReader) -> dict:
        """
        Gets the information from the given BinaryReader object.

        :param br: The BinaryReader object to get the information from.
        :return: A dictionary containing the information.
        """
        info = {}

        # Read all key values
        while br.remaining_bytes() > 0:
            key = br.read_string()

            if key == "":
                break

            info[key] = br.read_string().strip()

        return info

    def __get_players(self, br: BinaryReader) -> list:
        """
        Gets the players from the given BinaryReader object.

        :param br: The BinaryReader object to get the players from.
        :return: A list containing the players.
        """
        players = []

        # Skip a byte
        br.read_byte()

        # Get player count
        player_count = br.read_byte()

        # Get all keys
        keys = []

        while br.remaining_bytes() > 0:
            key = br.read_string()

            if key == "":
                break

            keys.append(key.rstrip("_"))

        # Set all keys and values
        for _ in range(player_count):
            players.append({key: br.read_string().strip() for key in keys})

        return players

    def __get_teams(self, br: BinaryReader) -> list:
        """
        Gets the teams from the given BinaryReader object.

        :param br: The BinaryReader object to get the teams from.
        :return: A list containing the teams.
        """
        teams = []

        # Skip a byte
        br.read_byte()

        # Get team count
        team_count = br.read_byte()

        # Get all keys
        keys = []

        while br.remaining_bytes() > 0:
            key = br.read_string()

            if key == "":
                break

            keys.append(key.rstrip("t").rstrip("_"))

        # Set all keys and values
        for _ in range(team_count):
            teams.append({key: br.read_string().strip() for key in keys})

        return teams


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # bfv
        gs2 = GameSpy2(host="108.61.236.22", port=23000, timeout=5.0)
        status = await gs2.get_status()
        print(status)

    asyncio.run(main_async())
