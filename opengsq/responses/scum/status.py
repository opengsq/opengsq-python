from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the response status of a server.
    """

    ip: str
    """The IP address of the server."""

    port: int
    """The port number of the server."""

    name: str
    """The name of the server."""

    num_players: int
    """The number of players currently connected to the server."""

    max_players: int
    """The maximum number of players that can connect to the server."""

    time: int
    """The server time."""

    password: bool
    """A value indicating whether a password is required to connect to the server."""

    version: str
    """The version of the server."""
