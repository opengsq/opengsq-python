from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Player:
    """
    Represents a player in the game.
    """

    name: Optional[str] = None
    """The name of the player."""

    team: Optional[str] = None
    """The team of the player."""

    skin: Optional[str] = None
    """The skin of the player."""

    score: Optional[int] = None
    """The score of the player."""

    ping: Optional[int] = None
    """The ping of the player."""

    time: Optional[int] = None
    """The time of the player."""
