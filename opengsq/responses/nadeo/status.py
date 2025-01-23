from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Player:
    """Represents a player on the server."""
    login: str
    nickname: str
    player_id: int
    team_id: int
    is_spectator: bool
    ladder_ranking: int
    flags: int
    

@dataclass
class ServerOptions:
    """Represents server configuration options."""
    name: str
    comment: str
    password: bool
    max_players: int
    max_spectators: int
    current_game_mode: int
    current_chat_time: int
    hide_server: int
    ladder_mode: int
    vehicle_quality: int


@dataclass
class Version:
    """Represents the server version information."""
    name: str
    version: str
    build: str


@dataclass
class Status:
    version: Version
    server_options: ServerOptions
    players: list[Player]
    map_info: MapInfo  # Add this
    
    @classmethod
    def from_raw_data(cls, version_data: dict[str, str], 
                    server_data: dict[str, Any], 
                    players_data: list[dict[str, Any]],
                    map_data: dict[str, Any]) -> Status:
        version = Version(
            name=version_data.get('Name', ''),
            version=version_data.get('Version', ''),
            build=version_data.get('Build', '')
        )
        
        server_options = ServerOptions(
            name=server_data.get('Name', ''),
            comment=server_data.get('Comment', ''),
            password=server_data.get('Password', False),
            max_players=server_data.get('CurrentMaxPlayers', 0),
            max_spectators=server_data.get('CurrentMaxSpectators', 0),
            current_game_mode=server_data.get('CurrentGameMode', 0),
            current_chat_time=server_data.get('CurrentChatTime', 0),
            hide_server=server_data.get('HideServer', 0),
            ladder_mode=server_data.get('CurrentLadderMode', 0),
            vehicle_quality=server_data.get('CurrentVehicleNetQuality', 0)
        )
        
        players = [
            Player(
                login=p.get('Login', ''),
                nickname=p.get('NickName', ''),
                player_id=p.get('PlayerId', -1),
                team_id=p.get('TeamId', -1),
                is_spectator=p.get('IsSpectator', False),
                ladder_ranking=p.get('LadderRanking', 0),
                flags=p.get('Flags', 0)
            )
            for p in players_data
        ]
        
        map_info = MapInfo.from_dict(map_data)

        return cls(version, server_options, players, map_info)
    
@dataclass
class MapInfo:
    """Represents current map information."""
    name: str
    author: str
    environment: str
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MapInfo:
        return cls(
            name=data.get('Name', ''),
            author=data.get('Author', ''),
            environment=data.get('Environment', '')
        )