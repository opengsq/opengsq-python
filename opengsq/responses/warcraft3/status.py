from dataclasses import dataclass
from typing import Dict, Any

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
    raw: Dict[str, Any] 