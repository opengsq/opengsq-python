from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class Player:
    """Represents a player in an ElDewrito server"""
    name: str
    uid: str = ""
    team: int = 0
    score: int = 0
    kills: int = 0
    assists: int = 0
    deaths: int = 0
    betrayals: int = 0
    time_spent_alive: int = 0
    suicides: int = 0
    best_streak: int = 0
    
@dataclass
class Status:
    """ElDewrito server status information"""
    name: str
    port: int
    file_server_port: int
    host_player: str
    sprint_state: str
    sprint_unlimited_enabled: str
    dual_wielding: str
    assassination_enabled: str
    vote_system_type: int
    teams: bool
    map: str
    map_file: str
    variant: str
    variant_type: str
    status: str
    num_players: int
    max_players: int
    mod_count: int
    mod_package_name: str
    mod_package_author: str
    mod_package_hash: str
    mod_package_version: str
    xnkid: str
    xnaddr: str
    players: List[Player]
    is_dedicated: bool
    game_version: str
    eldewrito_version: str