from dataclasses import dataclass
from typing import List, Dict, Any
from opengsq.responses.warcraft3.player import Player

@dataclass
class Status:
    """
    Represents the status of a Warcraft 3 game server.
    """
    game_version: str
    hostname: str
    map_name: str
    game_type: str
    num_players: int
    max_players: int
    players: List[Player]
    raw: Dict[str, Any] 