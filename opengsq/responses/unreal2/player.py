from dataclasses import dataclass


@dataclass
class Player:
    """
    Represents a player in the game.
    """

    id: int
    """The ID of the player."""

    name: str
    """The name of the player."""

    ping: int
    """The ping of the player."""

    score: int
    """The score of the player."""

    stats_id: int
    """The stats ID of the player."""
