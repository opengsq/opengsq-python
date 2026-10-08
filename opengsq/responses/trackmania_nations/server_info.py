from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

# TrackMania text formatting: "$$" is a literal dollar sign, "$" + up to three hex
# digits is a colour, "$l[...]"/"$h[...]" carry a link target and every other
# "$x" is a single-character style code.
_FORMATTING_PATTERN = re.compile(
    r"\$(\$|[0-9a-fA-F]{1,3}|[lLhHpP]\[[^\]]*\]|.)", re.DOTALL
)


def strip_formatting(text: str) -> str:
    """Removes TrackMania formatting codes ($fff, $o, $l[...], ...) from a string."""
    return _FORMATTING_PATTERN.sub(
        lambda match: "$" if match.group(1) == "$" else "", text
    )


@dataclass
class Player:
    """A player connected to the server."""

    name: str
    """Nickname, including TrackMania formatting codes."""

    ladder_ranking: int
    """Ladder ranking (-1 = not ranked, 0 = unknown)."""


@dataclass
class Challenge:
    """A challenge (map) of the server playlist."""

    name: str
    """Challenge name. The server truncates it to 15 characters."""

    gold_time: int
    """Gold medal time in milliseconds."""

    copper_price: int
    """Copper price (display cost) of the challenge."""

    environment: str
    """Environment (collection) of the challenge, e.g. Stadium."""


@dataclass
class ServerInfo:
    """
    Trackmania Nations/United Forever Server Information
    """

    name: str
    """Name of the server, including TrackMania formatting codes."""

    map: str
    """Current challenge (truncated to 15 characters by the server)."""

    players: int
    """Current number of players on the server."""

    max_players: int
    """Maximum number of players the server can hold."""

    game_mode: str
    """Current game mode (TimeAttack, Rounds, Team, Laps, Stunts or Cup)."""

    password_protected: bool = False
    """Whether joining as player requires a password."""

    version: str | None = None
    """Not part of the query response, always None."""

    environment: str = "Unknown"
    """Environment of the current challenge, e.g. Stadium."""

    comment: str = ""
    """Server comment."""

    server_login: str = ""
    """Login of the server host. In LAN mode this is the computer name."""

    pc_guid: str = ""
    """Deprecated alias of server_login."""

    time_limit: int = 0
    """Time limit in milliseconds (TimeAttack and Stunts)."""

    nb_laps: int = 0
    """Number of laps (Laps mode)."""

    spectator_slots: int = 0
    """Deprecated alias of max_spectators."""

    build_number: int = 0
    """Not part of the query response, always 0."""

    private_server: bool = False
    """Deprecated alias of password_protected."""

    ladder_server: bool = False
    """Whether the ladder mode is active (ladder_mode != 0)."""

    status_flags: int = 0
    """Not part of the query response, always 0."""

    challenge_crc: int = 0
    """Not part of the query response, always 0."""

    public_ip: str = ""
    """Not part of the query response, always empty."""

    local_ip: str = ""
    """Deprecated alias of server_address."""

    spectators: int = 0
    """Current number of spectators."""

    max_spectators: int = 0
    """Maximum number of spectators."""

    spectator_password_protected: bool = False
    """Whether joining as spectator requires a password."""

    ladder_mode: int = 0
    """Ladder mode (0 = inactive, 1 = forced)."""

    game_mode_id: int = 0
    """Internal game mode id (1 TimeAttack, 3 Rounds, 6 Team, 7 Laps, 8 Stunts, 9 Cup)."""

    points_limit: int = 0
    """Points limit (Rounds, Team and Cup)."""

    pack_mask: str = ""
    """Pack mask of the server, e.g. Stadium for Nations servers."""

    nb_challenges: int = 0
    """Number of challenges in the playlist (capped at 255 by the server)."""

    challenges: list[Challenge] = field(default_factory=list)
    """Current challenge followed by the next ones (at most 20)."""

    player_list: list[Player] = field(default_factory=list)
    """Players connected to the server."""

    server_address: str = ""
    """IP address the server announces for itself."""

    server_port: int = 0
    """Port the server announces for itself."""

    raw_data: str | None = field(default=None, repr=False)
    """Decompressed server info payload as hex string."""

    @property
    def plain_name(self) -> str:
        """Server name without TrackMania formatting codes."""
        return strip_formatting(self.name)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the server info.
        """
        return (
            f"Trackmania Nations Server: {self.plain_name}\n"
            f"Map: {self.map} ({self.environment})\n"
            f"Players: {self.players}/{self.max_players}\n"
            f"Spectators: {self.spectators}/{self.max_spectators}\n"
            f"Game Mode: {self.game_mode}\n"
            f"Password Protected: {self.password_protected}\n"
            f"Comment: {self.comment}"
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization, excluding raw_data.
        """
        result = asdict(self)
        result.pop("raw_data", None)
        return result
