from dataclasses import dataclass


@dataclass
class StatusPre17:
    """
    Represents the status of a game for versions prior to 1.7.
    """

    protocol: str
    """The protocol of the game."""

    version: str
    """The version of the game."""

    motd: str
    """The message of the day."""

    num_players: int
    """The number of players in the game."""

    max_players: int
    """The maximum number of players allowed in the game."""
