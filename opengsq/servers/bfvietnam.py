from time import time

from opengsq.interfaces import IServer
from opengsq.models import Player, Server
from opengsq.protocols import GS2


class BFVietnam(IServer):
    full_name = 'Battlefield Vietnam'

    def __init__(self, address: str, query_port: int = 23000, timeout: float = 5.0):
        super().__init__(address, query_port)
        self.protocol = GS2(address, query_port, timeout)

    async def query(self) -> Server:
        start_time = time()
        info = await self.protocol.get_info()
        latency = time() - start_time

        players = await self.protocol.get_players()
        teams = await self.protocol.get_teams()

        s = Server()
        s.ip = self.address
        s.query_port = self.query_port
        s.game_port = int(info['hostport'])
        s.name = info['hostname']
        s.map = info['mapname']
        s.password = info['password'] == '1'
        s.players = int(info['numplayers'])
        s.max_players = int(info['maxplayers'])
        s.bots = 0
        s.player_list = []
        s.latency = latency
        s.raw = {}
        s.raw['info'] = info
        s.raw['players'] = players
        s.raw['teams'] = teams

        for player in players:
            p = Player()
            p.name = player['player_'].strip()
            p.score = int(player['score_'])
            p.time = 0
            s.player_list.append(p)

        return s
