from dataclasses import dataclass

@dataclass
class Status:
    name: str
    map: str
    game_type: str
    num_players: int
    max_players: int
    password_protected: bool 