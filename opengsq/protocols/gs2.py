from opengsq.interfaces import IProtocol
from opengsq.protocols.binary_reader import BinaryReader
from opengsq.protocols.socket_async import SocketAsync


class GS2(IProtocol):
    full_name = 'Gamespy Query Protocol version 2'
    challenge = False

    class __Request():
        GS2_INFO = b'\xFF\x00\x00'
        GS2_PLAYERS = b'\x00\xFF\x00'
        GS2_TEAMS = b'\x00\x00\xFF'

    __PACKET_HEADER = b'\xFE\xFD\x00\x04\x05\x06\x07'

    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        self.__sock = None
        self.__address = address
        self.__query_port = query_port
        self.__timeout = timeout

    def __del__(self):
        self.__disconnect()

    async def __connect(self):
        self.__disconnect()
        self.__sock = SocketAsync()
        self.__sock.settimeout(self.__timeout)
        await self.__sock.connect((SocketAsync.gethostbyname(self.__address), self.__query_port))

    def __disconnect(self):
        if self.__sock:
            self.__sock.close()

    async def get_info(self) -> dict:
        await self.__connect()

        self.__sock.send(self.__PACKET_HEADER + self.__Request.GS2_INFO)
        response = await self.__sock.recv()
        br = BinaryReader(data=response[5:])

        info = {}

        while br.length() > 0:
            key = br.read_string()

            if key == '':
                break

            info[key] = br.read_string()

        return info

    async def get_players(self) -> dict:
        await self.__connect()

        self.__sock.send(self.__PACKET_HEADER + self.__Request.GS2_PLAYERS)
        response = await self.__sock.recv()

        br = BinaryReader(data=response[6:])
        player_count = br.read_byte()

        # Get all columns
        columns = []

        while br.length() > 0:
            column = br.read_string()

            if column == '':
                break

            columns.append(column)

        # Assign all values to columns
        players = []

        for i in range(player_count):
            player = {}

            for i in range(len(columns)):
                player[columns[i]] = br.read_string()

            players.append(player)

        return players

    async def get_teams(self) -> dict:
        await self.__connect()

        self.__sock.send(self.__PACKET_HEADER + self.__Request.GS2_TEAMS)
        response = await self.__sock.recv()

        br = BinaryReader(data=response[7:])

        # Get all columns
        columns = []

        while br.length() > 0:
            column = br.read_string()

            if column == '':
                break

            columns.append(column)

        # Assign all values to columns
        teams = []

        while br.length() > 0:
            team = {}

            for i in range(len(columns)):
                team[columns[i]] = br.read_string()

            teams.append(team)

        return teams


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs2 = GS2(address='', query_port=23000, timeout=5.0)
        info = await gs2.get_info()
        players = await gs2.get_players()
        teams = await gs2.get_teams()
        print(json.dumps(info, indent=None) + '\n')
        print(json.dumps(players, indent=None) + '\n')
        print(json.dumps(teams, indent=None) + '\n')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()
