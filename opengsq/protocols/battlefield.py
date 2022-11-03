from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync, SocketKind


class Battlefield(ProtocolBase):
    """Battlefield Protocol"""
    full_name = 'Battlefield Protocol'

    _info = b'\x00\x00\x00\x21\x1b\x00\x00\x00\x01\x00\x00\x00\x0a\x00\x00\x00serverInfo\x00'
    _version = b'\x00\x00\x00\x22\x18\x00\x00\x00\x01\x00\x00\x00\x07\x00\x00\x00version\x00'
    _players = b'\x00\x00\x00\x23\x24\x00\x00\x00\x02\x00\x00\x00\x0b\x00\x00\x00listPlayers\x00\x03\x00\x00\x00all\x00'

    async def get_info(self) -> dict:
        data = await self.__get_data(self._info)

        info = {}
        info['hostname'] = str(data.pop(0)).strip()
        info['numplayers'] = int(data.pop(0))
        info['maxplayers'] = int(data.pop(0))
        info['gametype'] = data.pop(0)
        info['map'] = data.pop(0)
        info['roundsplayed'] = int(data.pop(0))
        info['roundstotal'] = int(data.pop(0))
        num_teams = int(data.pop(0))
        info['teams'] = [float(data.pop(0)) for _ in range(num_teams)]
        info['targetscore'] = int(data.pop(0))
        info['status'] = data.pop(0)
        info['ranked'] = data.pop(0) == 'true'
        info['punkbuster'] = data.pop(0) == 'true'
        info['password'] = data.pop(0) == 'true'
        info['uptime'] = int(data.pop(0))
        info['roundtime'] = int(data.pop(0))

        try:
            if data[0] == 'BC2':
                info['mod'] = data.pop(0)
                data.pop(0)

            info['ip_port'] = data.pop(0)
            info['punkbuster_version'] = data.pop(0)
            info['join_queue'] = data.pop(0) == 'true'
            info['region'] = data.pop(0)
            info['pingsite'] = data.pop(0)
            info['country'] = data.pop(0)

            try:
                info['blaze_player_count'] = int(data[0])
                info['blaze_game_state'] = data[1]
            except Exception:
                info['quickmatch'] = data.pop(0) == 'true'
        except Exception:
            pass

        return info

    async def get_version(self) -> dict:
        data = await self.__get_data(self._version)
        return {'mod': data[0], 'version': data[1]}

    async def get_players(self) -> list:
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
        kind = SocketKind.SOCK_STREAM
        response = await SocketAsync.send_and_receive(self._address, self._query_port, self._timeout, request, kind)
        return self.__decode(response)

    def __decode(self, response: bytes):
        br = BinaryReader(response)
        br.read_long()  # header
        br.read_long()  # packet length
        count = br.read_long()  # string count
        data = []

        for _ in range(count):
            br.read_long()  # length of the string
            data.append(br.read_string())

        return data[1:]


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        entries = [
            ('91.206.15.69', 48888),  # bfbc2
            ('94.250.199.214', 47200),  # bf3
            ('74.91.124.140', 47200),  # bf4
            ('185.189.255.240', 47600),  # bfh
        ]

        for address, query_port in entries:
            battlefield = Battlefield(address, query_port, timeout=10.0)
            info = await battlefield.get_info()
            print(json.dumps(info, indent=None) + '\n')
            version = await battlefield.get_version()
            print(json.dumps(version, indent=None) + '\n')
            players = await battlefield.get_players()
            print(json.dumps(players, indent=None) + '\n')

    asyncio.run(main_async())
