from dataclasses import dataclass
from typing import Optional


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

    deaths: Optional[int] = None
    """Player Deaths"""

    money: Optional[int] = None
    """Player Money"""
