import json
from dataclasses import dataclass
from typing import List

from opengsq.protocols.models.player import Player


@dataclass()
class Server:
    name: str
    map: str
    players: int
    max_players: int
    bots: int
    latency: float
    player_list: List[Player]

    def __init__(self):
        pass

    def set_from_a2s(self, info: dict, players: list):
        self.name = info['Name']
        self.map = info['Map']
        self.players = info['Players']
        self.max_players = info['MaxPlayers']
        self.bots = info['Bots']
        self.player_list = []

        for player in players:
            p = Player()
            p.name = player['Name']
            p.score = player['Score']
            p.time = player['Duration']
            self.player_list.append(p)

    def to_json(self, *args, **kwargs):
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False, *args, **kwargs)
