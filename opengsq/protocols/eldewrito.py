import asyncio
import aiohttp
import json
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.eldewrito.status import Status, Player
from opengsq.binary_reader import BinaryReader
import struct
import logging

class ElDewrito(ProtocolBase):
    """ElDewrito Protocol Implementation"""
    
    ELDEWRITO_BROADCAST_PORT = 11774
    ELDEWRITO_HTTP_PORT = 11775
    
    # ElDewrito broadcast query payload
    BROADCAST_QUERY = bytes([
        0x01, 0x62, 0x6c, 0x61, 0x6d, 0x00, 0x00, 0x00, 
        0x09, 0x81, 0x00, 0x02, 0x00, 0x01, 0x2d, 0xc3, 
        0x04, 0x93, 0xdc, 0x05, 0xd9, 0x95, 0x40
    ])
    
    @property
    def full_name(self) -> str:
        return "ElDewrito Protocol"
    
    def __init__(self, host: str, port: int = ELDEWRITO_BROADCAST_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self._allow_broadcast = True
        self.logger = logging.getLogger(f"{__name__}.ElDewrito")
        
    async def get_status(self) -> Status:
        """
        Get server status using ElDewrito's two-step discovery process:
        1. Send broadcast query to port 11774
        2. Get HTTP response from port 11775
        """
        # Step 1: Send broadcast query and wait for response
        try:
            data = await UdpClient.communicate(
                self, 
                self.BROADCAST_QUERY, 
                source_port=self.ELDEWRITO_BROADCAST_PORT
            )
            
            # Step 2: Validate response (must be > 120 bytes from port 11774)
            if not self._is_valid_broadcast_response(data):
                raise Exception("Invalid broadcast response")
                
            # Step 3: Query HTTP endpoint for detailed server info
            server_info = await self._query_http_endpoint()
            
            # Step 4: Parse and return status
            return self._parse_server_info(server_info)
            
        except Exception as e:
            self.logger.error(f"Error getting ElDewrito server status: {e}")
            raise
    
    def _is_valid_broadcast_response(self, data: bytes) -> bool:
        """
        Validate ElDewrito broadcast response.
        Response should be > 120 bytes and from port 11774.
        """
        return len(data) > 120
    
    async def _query_http_endpoint(self) -> dict:
        """
        Query the ElDewrito HTTP endpoint on port 11775 for server information.
        """
        url = f"http://{self._host}:{self.ELDEWRITO_HTTP_PORT}/"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"HTTP request failed with status {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error querying HTTP endpoint: {e}")
            raise
    
    def _parse_server_info(self, server_info: dict) -> Status:
        """
        Parse the JSON response from ElDewrito HTTP endpoint into Status object.
        """
        try:
            # Parse players list
            players = []
            for player_data in server_info.get('players', []):
                player = Player(
                    name=player_data.get('name', ''),
                    uid=player_data.get('uid', ''),
                    team=player_data.get('team', 0),
                    score=player_data.get('score', 0),
                    kills=player_data.get('kills', 0),
                    assists=player_data.get('assists', 0),
                    deaths=player_data.get('deaths', 0),
                    betrayals=player_data.get('betrayals', 0),
                    time_spent_alive=player_data.get('timeSpentAlive', 0),
                    suicides=player_data.get('suicides', 0),
                    best_streak=player_data.get('bestStreak', 0)
                )
                players.append(player)
            
            # Create Status object
            status = Status(
                name=server_info.get('name', 'Unknown ElDewrito Server'),
                port=server_info.get('port', self.ELDEWRITO_BROADCAST_PORT),
                file_server_port=server_info.get('fileServerPort', 11778),
                host_player=server_info.get('hostPlayer', ''),
                sprint_state=server_info.get('sprintState', '2'),
                sprint_unlimited_enabled=server_info.get('sprintUnlimitedEnabled', '0'),
                dual_wielding=server_info.get('dualWielding', '1'),
                assassination_enabled=server_info.get('assassinationEnabled', '0'),
                vote_system_type=server_info.get('voteSystemType', 0),
                teams=server_info.get('teams', False),
                map=server_info.get('map', 'Unknown Map'),
                map_file=server_info.get('mapFile', ''),
                variant=server_info.get('variant', 'none'),
                variant_type=server_info.get('variantType', 'none'),
                status=server_info.get('status', 'Unknown'),
                num_players=server_info.get('numPlayers', 0),
                max_players=server_info.get('maxPlayers', 16),
                mod_count=server_info.get('modCount', 0),
                mod_package_name=server_info.get('modPackageName', ''),
                mod_package_author=server_info.get('modPackageAuthor', ''),
                mod_package_hash=server_info.get('modPackageHash', ''),
                mod_package_version=server_info.get('modPackageVersion', ''),
                xnkid=server_info.get('xnkid', ''),
                xnaddr=server_info.get('xnaddr', ''),
                players=players,
                is_dedicated=server_info.get('isDedicated', True),
                game_version=server_info.get('gameVersion', 'Unknown'),
                eldewrito_version=server_info.get('eldewritoVersion', 'Unknown')
            )
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error parsing server info: {e}")
            raise Exception(f"Failed to parse ElDewrito server info: {e}")
    
    async def discover_servers(self, broadcast_address: str = "255.255.255.255") -> list:
        """
        Discover ElDewrito servers using broadcast query.
        This method can be used for network discovery.
        """
        discovered_servers = []
        
        try:
            # Create a temporary instance for broadcast
            broadcast_client = ElDewrito(broadcast_address, self.ELDEWRITO_BROADCAST_PORT, self._timeout)
            
            # Send broadcast query - use regular communicate method
            data = await UdpClient.communicate(
                broadcast_client,
                self.BROADCAST_QUERY,
                source_port=self.ELDEWRITO_BROADCAST_PORT
            )
            
            # Process response if valid
            if self._is_valid_broadcast_response(data):
                try:
                    # Create client for specific server
                    server_client = ElDewrito(broadcast_address, self.ELDEWRITO_BROADCAST_PORT, self._timeout)
                    status = await server_client.get_status()
                    discovered_servers.append(((broadcast_address, self.ELDEWRITO_BROADCAST_PORT), status))
                except Exception as e:
                    self.logger.debug(f"Failed to get status from {broadcast_address}:{self.ELDEWRITO_BROADCAST_PORT}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during server discovery: {e}")
            
        return discovered_servers 