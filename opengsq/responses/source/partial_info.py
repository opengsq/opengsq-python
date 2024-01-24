from dataclasses import dataclass
from .server_type import ServerType
from .environment import Environment
from .visibility import Visibility
from .vac import VAC


@dataclass
class PartialInfo:
    """
    A2S_INFO Partial Info
    """

    protocol: int
    """Protocol version used by the server."""

    name: str
    """Name of the server."""

    map: str
    """Map the server has currently loaded."""

    folder: str
    """Name of the folder containing the game files."""

    game: str
    """Full name of the game."""

    players: int
    """Number of players on the server."""

    max_players: int
    """Maximum number of players the server reports it can hold."""

    bots: int
    """Number of bots on the server."""

    server_type: ServerType
    """Indicates the type of server."""

    environment: Environment
    """Indicates the operating system of the server."""

    visibility: Visibility
    """Indicates whether the server requires a password."""

    vac: VAC
    """Specifies whether the server uses VAC."""
