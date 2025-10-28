from dataclasses import dataclass
from .info import Info
from .status import Status


@dataclass
class Cod1Status:
    """
    Represents the combined status information from a Call of Duty 1 server.
    Contains both info and status responses.
    """

    info: Info
    """The server info response."""

    status: Status
    """The server status response."""
