from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status response from a server.
    """

    version: str
    """The version of the server."""

    password: bool
    """Indicates whether a password is required to connect to the server."""

    num_players: int
    """The number of players currently connected to the server."""

    max_players: int
    """The maximum number of players that can connect to the server."""

    server_name: str
    """The name of the server."""

    game_type: str
    """The type of game being played on the server."""

    language: str
    """The language of the server."""
