from dataclasses import dataclass
from typing import Union, List
from enum import IntEnum

class PlatformType(IntEnum):
    Unknown = 0
    Windows = 1
    Xenon = 4
    PS3 = 8
    Linux = 16
    MacOSX = 32

@dataclass
class Player:
    name: str
    score: int = 0
    ping: int = 0
    team: int = 0

@dataclass
class Status:
    name: str
    map: str
    game_type: str
    num_players: int
    max_players: int
    password_protected: bool
    stats_enabled: bool
    lan_mode: bool
    players: List[Player]
    raw: dict[str, Union[str, int, bool, list]]