from dataclasses import dataclass


@dataclass
class Player:
    """
    Player Data
    """

    name: str
    """Player Name"""

    score: int
    """Player Score"""

    duration: float
    """Player Duration"""

    deaths: int | None = None
    """Player Deaths"""

    money: int | None = None
    """Player Money"""
