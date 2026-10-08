from __future__ import annotations

from dataclasses import asdict, dataclass, field

from opengsq.responses.trackmania_nations import strip_formatting


@dataclass
class Player:
    """A player connected to the server."""

    name: str
    """Nickname, including TrackMania formatting codes."""

    ladder_ranking: int
    """Ladder ranking as sent by the server."""


@dataclass
class Challenge:
    """A challenge (map) of the server playlist."""

    name: str
    """Challenge name. The server truncates it to 15 characters."""

    gold_time: int
    """Gold medal time in milliseconds."""

    copper_price: int
    """Copper price (display cost) of the challenge."""

    decoration_index: int
    """
    2 + index of the challenge decoration (environment and mood) in the
    decoration table of the server, 0 if unknown. See TrackmaniaSunrise.decoration().
    """

    environment: str = ""
    """Environment of the challenge, e.g. Island. Empty if the game is unknown."""

    mood: str = ""
    """Decoration (mood) of the challenge, e.g. Night. Empty if unknown."""


@dataclass
class ServerInfo:
    """
    TrackMania Original/Sunrise/Nations ESWC Server Information
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
    """Current game mode (TimeAttack, Rounds, Team, Laps or Stunts)."""

    game_id: str = ""
    """
    Game the server runs. TmNationsESWC is recognised by the game tag,
    TmOriginal and TmSunrise only when passed to get_info() (use get_session()
    to find out), otherwise it is empty.
    """

    environment: str = ""
    """Environment of the current challenge, e.g. Island. Empty if the game is unknown."""

    mood: str = ""
    """Decoration (mood) of the current challenge, e.g. Night."""

    game_tag: int = 0
    """Game tag of the server info (0x07 Original/Sunrise, 0x09 Nations ESWC)."""

    protocol_version: int = 0
    """ConnectionAdmin version of the server (4 Original/Sunrise, 5 Nations ESWC)."""

    password_protected: bool = False
    """Whether joining as player requires a password."""

    spectator_password_protected: bool = False
    """Whether joining as spectator requires a password."""

    spectators: int = 0
    """Current number of spectators."""

    max_spectators: int = 0
    """Maximum number of spectators."""

    ladder_mode: int = 0
    """Ladder mode (0 = inactive)."""

    ladder_server: bool = False
    """Whether the ladder mode is active (ladder_mode != 0)."""

    comment: str = ""
    """Server comment."""

    server_login: str = ""
    """Login of the server host. In LAN mode this is the computer name."""

    server_address: str = ""
    """IP address the server announces for itself."""

    server_port: int = 0
    """Port the server announces for itself."""

    game_mode_id: int = 0
    """Internal game mode id (1 TimeAttack, 3 Rounds, 6 Team, 7 Laps, 8 Stunts)."""

    time_limit: int = 0
    """Time limit in milliseconds (TimeAttack and Stunts)."""

    nb_laps: int = 0
    """Number of laps (Laps mode)."""

    points_limit: int = 0
    """Points limit (Rounds and Team)."""

    nb_challenges: int = 0
    """Number of challenges in the playlist (capped at 255 by the server)."""

    challenges: list[Challenge] = field(default_factory=list)
    """Current challenge followed by the next ones (at most 20)."""

    player_list: list[Player] = field(default_factory=list)
    """Players connected to the server."""

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
            f"TrackMania Server: {self.plain_name}\n"
            f"Map: {self.map} ({self.environment or 'Unknown'})\n"
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


@dataclass
class SessionInfo:
    """
    LAN session announced by a server in reply to a session query
    (CNetFormEnumSessions).
    """

    game_id: str
    """Game the server runs: TmOriginal, TmSunrise or TmNationsESWC."""

    game: str
    """Name of the game, e.g. TrackMania Sunrise."""

    version: str
    """Version string of the server's network layer, e.g. 1.043."""

    host_name: str
    """Computer name of the server host."""

    application: str
    """Name of the network application, GameNet for the game server."""

    server_address: str
    """IP address the server announces for itself."""

    server_port: int
    """Game port the server announces for itself."""

    secondary_address: str = ""
    """Second address announced by the server (usually the same)."""

    secondary_port: int = 0
    """Port of the second announced address."""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
