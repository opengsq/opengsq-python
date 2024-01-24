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

    link: str
    """URL to mod website."""

    download_link: str
    """URL to download the mod."""

    version: int
    """Version of mod installed on server."""

    size: int
    """Space (in bytes) the mod takes up."""

    type: int
    """
    Indicates the type of mod:
    0 for single and multiplayer mod
    1 for multiplayer only mod
    """

    dll: int
    """
    Indicates whether mod uses its own DLL:
    0 if it uses the Half-Life DLL
    1 if it uses its own DLL
    """
