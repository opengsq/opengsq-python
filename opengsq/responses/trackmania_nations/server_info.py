from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServerInfo:
    """
    Trackmania Nations Server Information
    Erweitert basierend auf Reverse-Engineering der #SRV# Server-Announcement-Payloads
    """

    name: str
    """Name of the server."""

    map: str
    """Current map being played."""

    players: int
    """Current number of players on the server."""

    max_players: int
    """Maximum number of players the server can hold."""

    game_mode: str
    """Current game mode (e.g., Time Attack, Rounds, Cup, etc.)."""

    password_protected: bool = False
    """Whether the server requires a password."""

    version: Optional[str] = None
    """Server/game version."""

    # Erweiterte Felder aus der Dokumentation
    environment: str = "Unknown"
    """Map environment (Stadium, Canyon, Valley, etc.)."""

    comment: str = ""
    """Server comment/description."""

    server_login: str = ""
    """Server login name."""

    pc_guid: str = ""
    """PC GUID identifier."""

    time_limit: int = 0
    """Time limit in milliseconds."""

    nb_laps: int = 0
    """Number of laps for lap-based modes."""

    spectator_slots: int = 0
    """Maximum number of spectator slots."""

    build_number: int = 0
    """Game build number."""

    private_server: bool = False
    """Whether the server is private."""

    ladder_server: bool = False
    """Whether the server is a ladder server."""

    status_flags: int = 0
    """Server status flags bitfield."""

    challenge_crc: int = 0
    """Challenge/Map CRC checksum."""

    public_ip: str = ""
    """Public IP address of the server."""

    local_ip: str = ""
    """Local IP address of the server."""

    raw_data: Optional[str] = field(default=None, repr=False)
    """Raw response data from the server as hex string."""

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the server info.
        """
        return (
            f"Trackmania Nations Server: {self.name}\n"
            f"Map: {self.map} ({self.environment})\n"
            f"Players: {self.players}/{self.max_players}\n"
            f"Game Mode: {self.game_mode}\n"
            f"Password Protected: {self.password_protected}\n"
            f"Version: {self.version}\n"
            f"Comment: {self.comment}"
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization, excluding raw_data.
        """
        return {
            'name': self.name,
            'map': self.map,
            'players': self.players,
            'max_players': self.max_players,
            'game_mode': self.game_mode,
            'password_protected': self.password_protected,
            'version': self.version,
            'environment': self.environment,
            'comment': self.comment,
            'server_login': self.server_login,
            'pc_guid': self.pc_guid,
            'time_limit': self.time_limit,
            'nb_laps': self.nb_laps,
            'spectator_slots': self.spectator_slots,
            'build_number': self.build_number,
            'private_server': self.private_server,
            'ladder_server': self.ladder_server,
            'status_flags': self.status_flags,
            'challenge_crc': self.challenge_crc,
            'public_ip': self.public_ip,
            'local_ip': self.local_ip
        }
