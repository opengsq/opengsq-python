import re

from opengsq.interfaces import IProtocol
from opengsq.protocols.binary_reader import BinaryReader
from opengsq.protocols.socket_async import SocketAsync


class GS1(IProtocol):
    full_name = 'Gamespy Query Protocol version 1'
    challenge = False

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

        self.__sock.send(b'\\info\\')

        info = {}
        loop_packets = True

        # Receive packets until b'final\\'
        while loop_packets:
            response = await self.__sock.recv()
            br = BinaryReader(data=response[1:])

            while br.length() > 0:
                key = br.read_string(read_until=b'\\')

                if key == 'queryid':
                    br.read_string(read_until=b'\\')

                    if br.read() == b'final\\':
                        loop_packets = False

                    break

                value = br.read_string(read_until=b'\\')
                info[key] = value.strip()

        return info

    async def get_players(self) -> dict:
        await self.__connect()

        self.__sock.send(b'\\players\\')

        players = []
        old_index = -1
        loop_packets = True

        # Receive packets until b'final\\'
        while loop_packets:
            response = await self.__sock.recv()
            br = BinaryReader(data=response[1:])

            while br.length() > 0:
                key = br.read_string(read_until=b'\\')

                if key == 'queryid':
                    br.read_string(read_until=b'\\')

                    if br.read() == b'final\\':
                        loop_packets = False

                    break

                matches = re.search(r'(.+?)_(\d+)', key)
                name = matches.group(1)
                index = int(matches.group(2))

                if old_index != index:
                    old_index = index
                    players.append({})

                value = br.read_string(read_until=b'\\')
                players[index][name] = value.strip()

        return players

    async def get_teams(self) -> dict:
        await self.__connect()

        self.__sock.send(b'\\teams\\')

        teams = []
        old_index = -1
        loop_packets = True

        # Receive packets until b'final\\'
        while loop_packets:
            response = await self.__sock.recv()
            br = BinaryReader(data=response[1:])

            while br.length() > 0:
                key = br.read_string(read_until=b'\\')

                if key == 'queryid':
                    br.read_string(read_until=b'\\')

                    if br.read() == b'final\\':
                        loop_packets = False

                    break

                matches = re.search(r'(.+?)_(\d+)', key)
                name = matches.group(1)
                index = int(matches.group(2))

                if old_index != index:
                    old_index = index
                    teams.append({})

                value = br.read_string(read_until=b'\\')
                teams[index][name] = value.strip()

        return teams


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs1 = GS1(address='', query_port=7778, timeout=5.0)
        info = await gs1.get_info()
        players = await gs1.get_players()
        teams = await gs1.get_teams()
        print(json.dumps(info, indent=None) + '\n')
        print(json.dumps(players, indent=None) + '\n')
        print(json.dumps(teams, indent=None) + '\n')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()
