from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
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

    link: Optional[str] = None
    """URL to mod website."""

    download_link: Optional[str] = None
    """URL to download the mod."""

    version: Optional[int] = None
    """Version of mod installed on server."""

    size: Optional[int] = None
    """Space (in bytes) the mod takes up."""

    type: Optional[int] = None
    """
    Indicates the type of mod:
    0 for single and multiplayer mod
    1 for multiplayer only mod
    """

    dll: Optional[int] = None
    """
    Indicates whether mod uses its own DLL:
    0 if it uses the Half-Life DLL
    1 if it uses its own DLL
    """
