from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status response.
    """

    state: int
    """The state."""

    num_players: int
    """The number of players currently connected to the server."""

    max_players: int
    """The maximum number of players that can connect to the server."""
 
    name: str
    """The name of the server."""
