from dataclasses import dataclass
from typing import Union, List
from enum import IntEnum


class DirectPlayGameType(IntEnum):
    """DirectPlay Game Types"""

    UNKNOWN = 0
    AGE_OF_EMPIRES_1 = 1
    AGE_OF_EMPIRES_2 = 2


@dataclass
class Player:
    """DirectPlay Player Information"""

    name: str
    civilization: str = ""
    team: int = 0
    color: int = 0
    ready: bool = False


@dataclass
class Status:
    """DirectPlay Status Response"""

    name: str
    game_type: str
    map: str
    num_players: int
    max_players: int
    password_protected: bool
    game_version: str
    game_mode: str
    difficulty: str
    speed: str
    players: List[Player]
    raw: dict[str, Union[str, int, bool, list]]
