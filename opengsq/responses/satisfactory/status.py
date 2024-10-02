from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status response.
    """

    state: int
    """The state."""

    name: str
    """The name of the server."""

    num_players: int
    """The number of players in the game."""

    max_players: int
    """The maximum number of players allowed in the game."""
