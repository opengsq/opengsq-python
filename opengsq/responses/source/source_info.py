from dataclasses import dataclass
from typing import Optional
from .partial_info import PartialInfo
from .extra_data_flag import ExtraDataFlag


@dataclass
class SourceInfo(PartialInfo):
    """
    Source Response
    """

    id: int
    """Steam Application ID of game."""

    version: str
    """Version of the game installed on the server."""

    edf: Optional[ExtraDataFlag] = None
    """If present, this specifies which additional data fields will be included."""

    port: Optional[int] = None
    """The server's game port number."""

    steam_id: Optional[int] = None
    """Server's SteamID."""

    spectator_port: Optional[int] = None
    """Spectator port number for SourceTV."""

    spectator_name: Optional[str] = None
    """Name of the spectator server for SourceTV."""

    keywords: Optional[str] = None
    """Tags that describe the game according to the server (for future use.)"""

    game_id: Optional[int] = None
    """The server's 64-bit GameID. If this is present, a more accurate AppID is present in the low 24 bits. The earlier AppID could have been truncated as it was forced into 16-bit storage."""

    mode: Optional[int] = None
    """Indicates the game mode."""

    witnesses: Optional[int] = None
    """The number of witnesses necessary to have a player arrested."""

    duration: Optional[int] = None
    """Time (in seconds) before a player is arrested while being witnessed."""
