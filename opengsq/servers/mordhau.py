from time import time

from opengsq.interfaces import IServer
from opengsq.models import Server
from opengsq.protocols import A2S


class Mordhau(IServer):
    full_name = 'Mordhau'

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address, query_port)
        self.protocol = A2S(address, query_port, timeout, A2S.SOURCE)

    async def query(self) -> Server:
        start_time = time()
        info = await self.protocol.get_info()
        latency = time() - start_time

        s = Server()
        s.ip = self.address
        s.query_port = self.query_port
        s.game_port = int(info['GamePort'])
        s.name = info['Name']
        s.map = info['Map']
        s.password = info['Visibility'] == 1
        s.players = info['Players']

        # Fix player count
        for sub in str(info['Keywords']).split(','):
            if sub.startswith('B:'):
                s.players = int(sub[2:])
                break

        s.max_players = info['MaxPlayers']
        s.bots = info['Bots']
        s.player_list = []
        s.raw = {}
        s.raw['info'] = info

        s.latency = latency

        return s
