from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status response from a Minecraft server.
    """

    edition: str
    """The edition of the server (MCPE or MCEE for Education Edition)."""

    motd_line1: str
    """The first line of the Message of the Day (MOTD)."""

    protocol_version: int
    """The protocol version of the server."""

    version_name: str
    """The version name of the server."""

    num_players: int
    """The number of players currently on the server."""

    max_players: int
    """The maximum number of players that can join the server."""

    server_unique_id: str
    """The unique ID of the server."""

    motd_line2: str
    """The second line of the Message of the Day (MOTD)."""

    game_mode: str
    """The game mode of the server."""

    game_mode_numeric: int
    """The numeric representation of the game mode."""

    port_ipv4: int
    """The IPv4 port of the server."""

    port_ipv6: int
    """The IPv6 port of the server."""
