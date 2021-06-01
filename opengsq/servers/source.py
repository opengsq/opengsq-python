from time import time

from opengsq.interfaces import IServer
from opengsq.models import Player, Server
from opengsq.protocols import A2S


class Source(IServer):
    full_name = ''

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0, engine=A2S.SOURCE):
        super().__init__(address, query_port)
        self.protocol = A2S(address, query_port, timeout, engine)

    async def query(self) -> Server:
        start_time = time()
        info = await self.protocol.get_info()
        latency = time() - start_time

        players = await self.protocol.get_players()

        s = Server()
        s.ip = self.address
        s.query_port = self.query_port

        if 'GamePort' in info:
            s.game_port = int(info['GamePort'])
        else:
            s.game_port = None

        s.name = info['Name']
        s.map = info['Map']
        s.password = info['Visibility'] == 1
        s.players = info['Players']
        s.max_players = info['MaxPlayers']
        s.bots = info['Bots']
        s.player_list = []
        s.raw = {}
        s.raw['info'] = info
        s.raw['players'] = players

        for player in players:
            p = Player()
            p.name = player['Name']
            p.score = player['Score']
            p.time = player['Duration']
            s.player_list.append(p)

        s.latency = latency

        return s
