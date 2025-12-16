from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Status:
    """
    Represents the status of a Supreme Commander game server.
    
    Attributes:
        game_name: Name of the game lobby
        hosted_by: Name of the host player
        product_code: Product code (SC1 = Supreme Commander, SCFA = Forged Alliance)
        scenario_file: Path to the map/scenario file
        num_players: Current number of players
        max_players: Maximum number of players (from map lookup table)
        map_width: Map width in game units (from lookup table, 0 if unknown)
        map_height: Map height in game units (from lookup table, 0 if unknown)
        map_name_lookup: Map name from lookup table (empty if unknown)
        game_speed: Game speed setting (slow/normal/fast)
        victory_condition: Victory condition type
        fog_of_war: Fog of war setting
        unit_cap: Unit cap setting
        cheats_enabled: Whether cheats are enabled
        team_lock: Team lock setting
        team_spawn: Team spawn setting
        allow_observers: Whether observers are allowed
        no_rush_option: No rush timer setting
        prebuilt_units: Prebuilt units setting
        civilian_alliance: Civilian alliance setting
        timeouts: Number of allowed timeouts
        options: Full options dictionary
        raw: Raw response data for debugging
    """
    game_name: str
    hosted_by: str
    product_code: str
    scenario_file: str
    num_players: int
    max_players: int = 8
    map_width: int = 0
    map_height: int = 0
    map_name_lookup: str = ""
    game_speed: str = "normal"
    victory_condition: str = "demoralization"
    fog_of_war: str = "explored"
    unit_cap: str = "500"
    cheats_enabled: bool = False
    team_lock: str = "unlocked"
    team_spawn: str = "random"
    allow_observers: bool = True
    no_rush_option: str = "Off"
    prebuilt_units: str = "Off"
    civilian_alliance: str = "enemy"
    timeouts: str = "3"
    options: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def map_name(self) -> str:
        """
        Get the map name.
        
        Prefers the lookup table name (map_name_lookup) if available,
        otherwise falls back to extracting from scenario file path.
        """
        # Try to get name from lookup table
        if self.map_name_lookup:
            return self.map_name_lookup
        
        # Fallback: extract from scenario file path
        if not self.scenario_file:
            return "Unknown Map"
        
        # Extract filename from path like "/maps/scmp_039/scmp_039_scenario.lua"
        parts = self.scenario_file.replace('\\', '/').split('/')
        if len(parts) >= 2:
            # Return the map folder name
            return parts[-2] if parts[-2] else parts[-1].replace('_scenario.lua', '')
        return self.scenario_file
    
    @property
    def map_id(self) -> str:
        """Extract map ID from scenario file path (e.g., 'scmp_039')"""
        if not self.scenario_file:
            return ""
        
        import re
        match = re.search(r'(scmp_\d+|x1mp_\d+)', self.scenario_file.lower())
        return match.group(1) if match else ""
    
    @property
    def players_display(self) -> str:
        """Get formatted player count string (handles unknown max_players)"""
        if self.max_players == 0:
            return f"{self.num_players}/?"
        return f"{self.num_players}/{self.max_players}"
    
    @property  
    def max_players_known(self) -> bool:
        """Check if max_players is known (from lookup table)"""
        return self.max_players > 0
    
    @property
    def map_size(self) -> Optional[tuple]:
        """
        Get the map size as (width, height) tuple in game units.
        
        Returns None if map is not in lookup table.
        Size units: 256=5km, 512=10km, 1024=20km, 2048=40km, 4096=80km
        """
        if self.map_width > 0 and self.map_height > 0:
            return (self.map_width, self.map_height)
        return None
    
    @property
    def map_size_km(self) -> Optional[tuple]:
        """
        Get the map size in kilometers as (width_km, height_km) tuple.
        
        Returns None if map is not in lookup table.
        """
        size = self.map_size
        if size:
            # 51.2 game units = 1 km
            return (size[0] / 51.2, size[1] / 51.2)
        return None
    
    @property
    def map_size_display(self) -> str:
        """
        Get a human-readable map size string.
        
        Returns format like "20x20 km" or "?" for unknown maps.
        """
        size_km = self.map_size_km
        if size_km:
            return f"{int(size_km[0])}x{int(size_km[1])} km"
        return "?"
    
    @property
    def map_size_category(self) -> str:
        """
        Get the map size category name.
        
        Categories:
        - 5x5 km: Tiny
        - 10x10 km: Small
        - 20x20 km: Medium
        - 40x40 km: Large
        - 80x80 km: Huge
        """
        size = self.map_size
        if not size:
            return "Unknown"
        
        width = size[0]
        if width <= 256:
            return "Tiny (5x5 km)"
        elif width <= 512:
            return "Small (10x10 km)"
        elif width <= 1024:
            return "Medium (20x20 km)"
        elif width <= 2048:
            return "Large (40x40 km)"
        else:
            return "Huge (80x80 km)"
    
    @property
    def game_title(self) -> str:
        """Get human-readable game title from product code"""
        titles = {
            'SC1': 'Supreme Commander',
            'SCFA': 'Supreme Commander: Forged Alliance',
            'SC2': 'Supreme Commander 2',
            'FAF': 'Forged Alliance Forever'
        }
        return titles.get(self.product_code, f'Supreme Commander ({self.product_code})')

