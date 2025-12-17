from dataclasses import dataclass
from .info import Info
from .status import Status


@dataclass
class JediKnightStatus:
    """
    Represents the combined status information from a Star Wars Jedi Knight - Jedi Academy server.
    Contains both info and status responses.
    """

    info: Info
    """The server info response."""

    status: Status
    """The server status response."""


