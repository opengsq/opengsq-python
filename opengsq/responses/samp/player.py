from dataclasses import dataclass


@dataclass
class Player:
    """
    Represents the Player class.
    """

    id: int
    """The ID of the player."""

    name: str
    """The name of the player."""

    score: int
    """The score of the player."""

    ping: int
    """The ping of the player."""
