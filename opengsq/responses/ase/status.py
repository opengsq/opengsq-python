from __future__ import annotations

from dataclasses import dataclass, field

from opengsq.responses.ase.player import Player


@dataclass
class Status:
    """
    Represents the status of a game server.
    """

    game_name: str
    """The name of the game."""

    game_port: int
    """The port number of the game server."""

    hostname: str
    """The hostname of the game server."""

    game_type: str
    """The type of the game."""

    map: str
    """The current map of the game."""

    version: str
    """The version of the game."""

    password: bool
    """Whether a password is required to join the game."""

    num_players: int
    """The number of players currently in the game."""

    max_players: int
    """The maximum number of players allowed in the game."""

    rules: dict[str, str] = field(default_factory=dict)
    """The rules of the game. Defaults to an empty dictionary."""

    players: list[Player] = field(default_factory=list)
    """The players currently in the game. Defaults to an empty list."""
