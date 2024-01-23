from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status response.
    """

    state: int
    """The state."""

    version: int
    """The version."""

    beacon_port: int
    """The beacon port."""
