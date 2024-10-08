from dataclasses import dataclass


@dataclass
class Player:
    """
    Represents a player in the game.
    """

    frags: int
    """The player's frags."""

    ping: int
    """The player's ping."""

    name: str
    """The player's name."""

    team: int
    """The player's team."""
