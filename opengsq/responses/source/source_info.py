from dataclasses import dataclass

from .extra_data_flag import ExtraDataFlag
from .partial_info import PartialInfo


@dataclass
class SourceInfo(PartialInfo):
    """
    Source Response
    """

    id: int
    """Steam Application ID of game."""

    version: str
    """Version of the game installed on the server."""

    edf: ExtraDataFlag | None = None
    """If present, this specifies which additional data fields will be included."""

    port: int | None = None
    """The server's game port number."""

    steam_id: int | None = None
    """Server's SteamID."""

    spectator_port: int | None = None
    """Spectator port number for SourceTV."""

    spectator_name: str | None = None
    """Name of the spectator server for SourceTV."""

    keywords: str | None = None
    """Tags that describe the game according to the server (for future use.)"""

    game_id: int | None = None
    """The server's 64-bit GameID. If this is present, a more accurate AppID is present in the low 24 bits. The earlier AppID could have been truncated as it was forced into 16-bit storage."""

    mode: int | None = None
    """Indicates the game mode."""

    witnesses: int | None = None
    """The number of witnesses necessary to have a player arrested."""

    duration: int | None = None
    """Time (in seconds) before a player is arrested while being witnessed."""
