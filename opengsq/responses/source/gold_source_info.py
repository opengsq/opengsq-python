from __future__ import annotations

from dataclasses import dataclass

from .partial_info import PartialInfo


@dataclass
class GoldSourceInfo(PartialInfo):
    """
    Obsolete GoldSource Response
    """

    address: str
    """IP address and port of the server."""

    mod: int
    """
    Indicates whether the game is a mod
    0 for Half-Life
    1 for Half-Life mod
    """

    link: str | None = None
    """URL to mod website."""

    download_link: str | None = None
    """URL to download the mod."""

    version: int | None = None
    """Version of mod installed on server."""

    size: int | None = None
    """Space (in bytes) the mod takes up."""

    type: int | None = None
    """
    Indicates the type of mod:
    0 for single and multiplayer mod
    1 for multiplayer only mod
    """

    dll: int | None = None
    """
    Indicates whether mod uses its own DLL:
    0 if it uses the Half-Life DLL
    1 if it uses its own DLL
    """
