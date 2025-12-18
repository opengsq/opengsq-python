from dataclasses import dataclass
from typing import List


@dataclass
class Status:
    """
    Represents the status response from a Warhammer 40K Dawn of War server broadcast.
    """

    guid: str = ""
    """Server GUID (unique identifier)."""

    hostname: str = ""
    """Server hostname/name."""

    current_players: int = 0
    """Current number of players."""

    max_players: int = 0
    """Maximum number of players."""

    ip_address: str = ""
    """Server IP address."""

    port: int = 6112
    """Server port (default: 6112)."""

    magic_marker: str = ""
    """Magic marker (should be 'WODW')."""

    build_number: int = 0
    """Build number (expected: 1001)."""

    version: str = ""
    """Game version (e.g., '1.51', '1.1')."""

    mod_name: str = ""
    """Mod/expansion identifier (w40k, wxp, dxp2)."""

    game_title: str = ""
    """Full game title."""

    map_scenario: str = ""
    """Map/scenario name."""

    faction_codes: List[str] = None
    """List of faction codes (8 factions)."""

    map_features: List[str] = None
    """List of map features."""

    def __post_init__(self):
        """Initialize mutable defaults after dataclass init."""
        if self.faction_codes is None:
            self.faction_codes = []
        if self.map_features is None:
            self.map_features = []

    @property
    def expansion_name(self) -> str:
        """
        Get the human-readable expansion name based on mod_name.

        :return: Expansion name
        """
        expansion_map = {
            "w40k": "Dawn of War",
            "wxp": "Winter Assault",
            "dxp2": "Dark Crusade",
            "dxp3": "Soulstorm",
        }
        return expansion_map.get(self.mod_name, self.mod_name)

    def __getattribute__(self, name):
        if name == "__dict__":
            # Create a custom dict that includes properties
            result = {}
            # Get the original __dict__ first
            original_dict = object.__getattribute__(self, "__dict__")
            result.update(original_dict)
            # Add the expansion name
            result["expansion_name"] = self.expansion_name
            return result
        return object.__getattribute__(self, name)

    def __init__(self, data: dict = None):
        """
        Initialize Status object from parsed data dictionary.

        :param data: Dictionary containing server status information
        """
        if data is None:
            data = {}

        # Set defaults first
        self.guid = ""
        self.hostname = ""
        self.current_players = 0
        self.max_players = 0
        self.ip_address = ""
        self.port = 6112
        self.magic_marker = ""
        self.build_number = 0
        self.version = ""
        self.mod_name = ""
        self.game_title = ""
        self.map_scenario = ""
        self.faction_codes = []
        self.map_features = []

        # Update with provided data
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
