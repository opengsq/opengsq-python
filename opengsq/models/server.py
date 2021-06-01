import json
from dataclasses import dataclass
from typing import List

from opengsq.models.player import Player


@dataclass()
class Server:
    ip: str
    query_port: int
    game_port: int
    name: str
    map: str
    password: bool
    players: int
    max_players: int
    bots: int
    latency: float
    player_list: List[Player]
    raw: dict

    def __init__(self):
        pass

    def to_json(self, *args, **kwargs):
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False, *args, **kwargs)
