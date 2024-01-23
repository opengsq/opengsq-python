from dataclasses import dataclass


@dataclass
class Player:
    """
    Represents a player in the game.
    """

    id: int
    """The player's ID."""

    score: int
    """The player's score."""

    time: int
    """The player's time."""

    ping: int
    """The player's ping."""

    name: str
    """The player's name."""

    skin: str
    """The player's skin."""

    color1: int
    """The player's first color."""

    color2: int
    """The player's second color."""
