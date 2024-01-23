from dataclasses import dataclass
from ..unreal2 import Status as Unreal2Status


@dataclass
class Status(Unreal2Status):
    """
    Represents the status of a server.
    """

    wave_current: int
    """The current wave number in a game."""

    wave_total: int
    """The total number of waves in a game."""
