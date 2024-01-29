from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass
class Status:
    """
    Represents the server status.
    """

    info: dict[str, str]
    """Server's info."""

    players: list[dict[str, Union[int, str]]]
    """Server's players."""
