from __future__ import annotations

from dataclasses import dataclass
from .player import Player


@dataclass
class Status:
    """
    Represents the status of the server.
    """

    info: dict[str, str]
    """The server information."""

    players: list[Player]
    """The list of players."""
