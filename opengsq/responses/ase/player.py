from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Player:
    """
    Represents a player in the game.
    """

    name: str
    """The name of the player."""

    team: str
    """The team of the player."""

    skin: str
    """The skin of the player."""

    score: int
    """The score of the player."""

    ping: int
    """The ping of the player."""

    time: int
    """The time of the player."""

    @property
    def __dict__(self):
        return asdict(self)
