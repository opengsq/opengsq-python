from __future__ import annotations
from typing import Optional
from dataclasses import dataclass


@dataclass
class Info:
    """
    Represents the info of a game.
    """

    hostname: str
    """The hostname of the game server."""

    num_players: int
    """The number of players in the game."""

    max_players: int
    """The maximum number of players allowed in the game."""

    game_type: str
    """The type of the game."""

    map: str
    """The current map of the game."""

    rounds_played: int
    """The number of rounds played."""

    rounds_total: int
    """The total number of rounds."""

    teams: list[float]
    """The list of teams."""

    target_score: int
    """The target score."""

    status: str
    """The status of the game."""

    ranked: bool
    """Whether the game is ranked."""

    punk_buster: bool
    """Whether PunkBuster is enabled."""

    password: bool
    """Whether a password is required."""

    uptime: int
    """The uptime of the game server."""

    round_time: int
    """The round time."""

    mod: Optional[str] = None
    """The game mod. This property is optional."""

    ip_port: Optional[str] = None
    """The IP port of the game server. This property is optional."""

    punk_buster_version: Optional[str] = None
    """The version of PunkBuster. This property is optional."""

    join_queue: Optional[bool] = None
    """Whether the join queue is enabled. This property is optional."""

    region: Optional[str] = None
    """The region of the game server. This property is optional."""

    ping_site: Optional[str] = None
    """The ping site of the game server. This property is optional."""

    country: Optional[str] = None
    """The country of the game server. This property is optional."""

    blaze_player_count: Optional[int] = None
    """The number of players in the Blaze game state. This property is optional."""

    blaze_game_state: Optional[str] = None
    """The Blaze game state. This property is optional."""

    quick_match: Optional[bool] = None
    """Whether quick match is enabled. This property is optional."""
