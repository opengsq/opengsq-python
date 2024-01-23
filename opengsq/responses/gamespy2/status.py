from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status of the server.
    """

    info: dict[str, str]
    """The server information."""

    players: list[dict[str, str]]
    """The list of players."""

    teams: list[dict[str, str]]
    """The list of teams."""
