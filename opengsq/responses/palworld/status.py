from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status response from a server.
    """

    num_players: int
    """The number of players currently connected to the server."""

    max_players: int
    """The maximum number of players that can connect to the server."""

    server_name: str
    """The name of the server."""