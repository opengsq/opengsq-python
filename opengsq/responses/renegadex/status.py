from dataclasses import dataclass
from typing import Any

@dataclass
class Variables:
    player_limit: int
    vehicle_limit: int
    mine_limit: int
    time_limit: int
    passworded: bool
    steam_required: bool
    team_mode: int
    spawn_crates: bool
    game_type: int
    ranked: bool
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Variables':
        return cls(
            player_limit=data["Player Limit"],
            vehicle_limit=data["Vehicle Limit"],
            mine_limit=data["Mine Limit"],
            time_limit=data["Time Limit"],
            passworded=data["bPassworded"],
            steam_required=data["bSteamRequired"],
            team_mode=data["Team Mode"],
            spawn_crates=data["bSpawnCrates"],
            game_type=data["Game Type"],
            ranked=data["bRanked"]
        )

@dataclass
class Status:
    name: str
    map: str
    port: int
    players: int
    game_version: str
    variables: Variables
    raw: dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Status':
        return cls(
            name=data["Name"],
            map=data["Current Map"],
            port=data["Port"],
            players=data["Players"],
            game_version=data["Game Version"],
            variables=Variables.from_dict(data["Variables"]),
            raw=data
        )