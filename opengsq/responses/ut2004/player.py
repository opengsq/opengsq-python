from dataclasses import dataclass


@dataclass
class Player:
    """
    Represents the player response(s) from an Unreal Tournament 2004 server.
    """

    name: str
    """Player Name"""

    frags: int
    """Player Score"""

    ping: int
    """Player Duration"""

    team: int
    """Player team"""
