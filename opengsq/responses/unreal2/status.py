from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status of a server.
    """

    server_id: int
    """The server ID."""

    server_ip: str
    """The IP address of the server."""

    game_port: int
    """The game port of the server."""

    query_port: int
    """The query port of the server."""

    server_name: str
    """The name of the server."""

    map_name: str
    """The name of the map."""

    game_type: str
    """The type of the game."""

    num_players: int
    """The number of players."""

    max_players: int
    """The maximum number of players."""

    ping: int
    """The ping."""

    flags: int
    """The flags."""

    skill: str
    """The skill level."""
