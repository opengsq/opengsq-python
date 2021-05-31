import json
from dataclasses import dataclass
from typing import List

from opengsq.protocols.models.player import Player


@dataclass()
class Server:
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
