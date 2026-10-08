from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the server status.
    """

    info: dict[str, str]
    """Server's info."""

    players: list[dict[str, int | str]]
    """Server's players."""
