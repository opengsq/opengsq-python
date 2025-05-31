from dataclasses import dataclass

@dataclass
class Player:
    """
    Represents a player in a Warcraft 3 game server.
    """
    name: str
    ping: int 