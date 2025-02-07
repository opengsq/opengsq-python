from dataclasses import dataclass

@dataclass
class Player:
    """
    Represents a player in the game.
    """

    name: str
    """The player's name."""

    ping: int
    """The player's ping."""

    level: int
    """The player's level."""
