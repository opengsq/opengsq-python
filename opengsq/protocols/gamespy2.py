from enum import Flag, auto

from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class GameSpy2(ProtocolBase):
    """GameSpy Protocol version 2"""
    full_name = 'GameSpy Protocol version 2'

    class Request(Flag):
        INFO = auto()
        PLAYERS = auto()
        TEAMS = auto()

    async def get_status(self, request: Request = Request.INFO | Request.PLAYERS | Request.TEAMS) -> dict:
        """Retrieves information about the server including, Info, Players, and Teams."""
        # Connect to remote host
        with SocketAsync() as sock:
            sock.settimeout(self._timeout)
            await sock.connect((self._address, self._query_port))

            # Send Request
            sock.send(b'\xFE\xFD\x00\x04\x05\x06\x07' + self.__get_request_bytes(request))

            # Server response
            response = await sock.recv()

        # Remove the first 5 bytes { 0x00, 0x04, 0x05, 0x06, 0x07 }
        br = BinaryReader(response[5:])

        status = {}

        if self.__has_flag(request, self.Request.INFO):
            status['info'] = self.__get_info(br)

        if self.__has_flag(request, self.Request.PLAYERS):
            status['players'] = self.__get_players(br)

        if self.__has_flag(request, self.Request.TEAMS):
            status['teams'] = self.__get_teams(br)

        return status

    def __get_request_bytes(self, request: Request):
        request_bytes = self.__has_flag(request, self.Request.INFO) and b'\xFF' or b'\x00'
        request_bytes += self.__has_flag(request, self.Request.PLAYERS) and b'\xFF' or b'\x00'
        request_bytes += self.__has_flag(request, self.Request.TEAMS) and b'\xFF' or b'\x00'

        return request_bytes

    def __has_flag(self, request, flag) -> bool:
        return request & flag == flag

    def __get_info(self, br: BinaryReader) -> dict:
        info = {}

        # Read all key values
        while br.length() > 0:
            key = br.read_string()

            if key == '':
                break

            info[key] = br.read_string().strip()

        return info

    def __get_players(self, br: BinaryReader) -> list:
        players = []

        # Skip a byte
        br.read_byte()

        # Get player count
        player_count = br.read_byte()

        # Get all keys
        keys = []

        while br.length() > 0:
            key = br.read_string()

            if key == '':
                break

            keys.append(key.rstrip('_'))

        # Set all keys and values
        for _ in range(player_count):
            players.append({key: br.read_string().strip() for key in keys})

        return players

    def __get_teams(self, br: BinaryReader) -> list:
        teams = []

        # Skip a byte
        br.read_byte()

        # Get team count
        team_count = br.read_byte()

        # Get all keys
        keys = []

        while br.length() > 0:
            key = br.read_string()

            if key == '':
                break

            keys.append(key.rstrip('t').rstrip('_'))

        # Set all keys and values
        for _ in range(team_count):
            teams.append({key: br.read_string().strip() for key in keys})

        return teams


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs2 = GameSpy2(address='158.69.118.94', query_port=23000, timeout=5.0)
        status = await gs2.get_status()
        print(json.dumps(status, indent=None) + '\n')

    asyncio.run(main_async())
