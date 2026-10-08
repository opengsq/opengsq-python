from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Player:
    """
    Represents a player in the game.
    """

    name: str | None = None
    """The name of the player."""

    team: str | None = None
    """The team of the player."""

    skin: str | None = None
    """The skin of the player."""

    score: int | None = None
    """The score of the player."""

    ping: int | None = None
    """The ping of the player."""

    time: int | None = None
    """The time of the player."""
