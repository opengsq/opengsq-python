from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VersionInfo:
    """
    Represents the version of a game mod.
    """

    mod: str
    """The mod of the game."""

    version: str
    """The version of the mod."""
