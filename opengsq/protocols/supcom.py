"""
Supreme Commander Protocol Implementation

This module implements the network discovery protocol for Supreme Commander games.
The protocol works by sending a UDP broadcast to port 15000 and receiving responses
from game servers.

Protocol Details:
- Request: UDP broadcast to port 15000 with payload 0x6e 0x03 0x00
- Response: Key-value pairs with 0x01 prefix for strings, null-terminated
- Local port: 55582 for receiving responses

Supported Games:
- Supreme Commander (SC1)
- Supreme Commander: Forged Alliance (SCFA)
"""

from __future__ import annotations

import struct
import asyncio
import socket
from typing import Dict, Any, Optional, List, Tuple

from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase
from opengsq.responses.supcom import Status


class SupCom(ProtocolBase):
    """
    Supreme Commander Protocol
    
    Implements the network discovery protocol for Supreme Commander games.
    Uses UDP broadcast on port 15000 with responses on port 55582.
    """
    
    full_name = "Supreme Commander Protocol"
    
    # Protocol constants
    QUERY_PORT = 15000           # Port to send broadcast queries to
    RESPONSE_PORT = 55582        # Local port to receive responses on
    
    # Request/Response markers
    REQUEST_MARKER = 0x6E        # 'n' - network query
    RESPONSE_MARKER = 0x6F       # 'o' - ok/output response
    STRING_TYPE = 0x01           # String value marker
    BLOCK_START = 0x04           # Start of options block
    BLOCK_END = 0x05             # End of block
    
    # Request payload
    QUERY_PAYLOAD = bytes([0x6E, 0x03, 0x00])  # 'n' + version 3 + terminator
    
    def __init__(self, host: str = "255.255.255.255", port: int = QUERY_PORT, timeout: float = 5.0):
        """
        Initialize the Supreme Commander protocol.
        
        Args:
            host: Target host or broadcast address (default: 255.255.255.255)
            port: Query port (default: 15000)
            timeout: Connection timeout in seconds (default: 5.0)
        """
        super().__init__(host, port, timeout)
    
    async def get_status(self) -> Status:
        """
        Query a Supreme Commander server for its status.
        
        For direct server queries (non-broadcast), sends a query to the specific
        host and port, then parses the response.
        
        Returns:
            Status: Parsed server status information
            
        Raises:
            Exception: If no response is received or parsing fails
        """
        response = await self._send_query()
        return self._parse_response(response)
    
    async def discover_servers(self, broadcast_addr: str = "255.255.255.255") -> List[Tuple[str, Status]]:
        """
        Discover Supreme Commander servers on the local network.
        
        Sends a UDP broadcast query and collects all responses.
        
        Args:
            broadcast_addr: Broadcast address to use (default: 255.255.255.255)
            
        Returns:
            List of tuples containing (server_ip, Status)
        """
        servers = []
        
        try:
            loop = asyncio.get_running_loop()
            responses = []
            
            # Create protocol for collecting responses
            class ResponseCollector(asyncio.DatagramProtocol):
                def __init__(self):
                    self.transport = None
                
                def connection_made(self, transport):
                    self.transport = transport
                
                def datagram_received(self, data: bytes, addr: Tuple[str, int]):
                    responses.append((data, addr))
                
                def error_received(self, exc):
                    pass
            
            # Create UDP socket on RESPONSE_PORT for both sending AND receiving
            # Supreme Commander servers respond to the source port of the query,
            # so we must send FROM port 55582, not just listen on it
            # Use SO_REUSEADDR to allow rapid re-binding after previous scan
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('0.0.0.0', self.RESPONSE_PORT))
            sock.setblocking(False)
            
            transport, protocol = await loop.create_datagram_endpoint(
                ResponseCollector,
                sock=sock
            )
            
            try:
                # Send broadcast query FROM port 55582
                transport.sendto(self.QUERY_PAYLOAD, (broadcast_addr, self.QUERY_PORT))
                
                # Wait for responses
                await asyncio.sleep(self._timeout)
                
                # Parse all responses
                for data, addr in responses:
                    try:
                        status = self._parse_response(data)
                        servers.append((addr[0], status))
                    except Exception:
                        continue
                        
            finally:
                transport.close()
                
        except Exception as e:
            raise Exception(f"Discovery failed: {e}")
        
        return servers
    
    async def _send_query(self) -> bytes:
        """
        Send a query to the configured host and receive the response.
        
        Returns:
            bytes: Raw response data
        """
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        
        class QueryProtocol(asyncio.DatagramProtocol):
            def __init__(self):
                self.transport = None
            
            def connection_made(self, transport):
                self.transport = transport
            
            def datagram_received(self, data: bytes, addr: Tuple[str, int]):
                if not response_future.done():
                    response_future.set_result(data)
            
            def error_received(self, exc):
                if not response_future.done():
                    response_future.set_exception(exc)
        
        # For broadcast queries, we need to listen on the response port
        is_broadcast = self._host in ('255.255.255.255', '<broadcast>')
        local_port = self.RESPONSE_PORT if is_broadcast else 0
        
        transport, protocol = await loop.create_datagram_endpoint(
            QueryProtocol,
            local_addr=('0.0.0.0', local_port),
            allow_broadcast=True
        )
        
        try:
            # Send query
            transport.sendto(self.QUERY_PAYLOAD, (self._host, self._port))
            
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=self._timeout)
            return response
            
        finally:
            transport.close()
    
    def _parse_response(self, data: bytes) -> Status:
        """
        Parse a Supreme Commander server response.
        
        The response format is:
        - Header: 0x6F (response marker) + 2 bytes length (little endian) + header info
        - Data: Key-value pairs with 0x01 prefix for strings
        
        Args:
            data: Raw response bytes
            
        Returns:
            Status: Parsed server status
            
        Raises:
            Exception: If response is invalid or parsing fails
        """
        if len(data) < 10:
            raise Exception(f"Response too short: {len(data)} bytes")
        
        # Verify response marker
        if data[0] != self.RESPONSE_MARKER:
            raise Exception(f"Invalid response marker: 0x{data[0]:02x}, expected 0x{self.RESPONSE_MARKER:02x}")
        
        # Parse header
        # Bytes 1-2: Length (little endian)
        response_length = struct.unpack('<H', data[1:3])[0]
        
        # Note: Byte 9 is NOT MaxPlayers - it's always 0x04 (block marker)
        # MaxPlayers is not sent in the protocol, we use a lookup table instead
        
        # Start parsing key-value pairs after header (offset 10)
        br = BinaryReader(data[10:])
        
        parsed_data: Dict[str, Any] = {}
        options: Dict[str, Any] = {}
        in_options_block = False
        
        while br.remaining_bytes() > 0:
            marker = br.read_byte()
            
            if marker == self.STRING_TYPE:
                # Read key
                key = br.read_string()
                
                if br.remaining_bytes() == 0:
                    break
                
                # Read value marker
                value_marker = br.read_byte()
                
                if value_marker == self.STRING_TYPE:
                    # String value
                    value = br.read_string()
                    
                    if in_options_block:
                        options[key] = value
                    else:
                        parsed_data[key] = value
                        
                elif value_marker == 0x00:
                    # Possibly a float value (4 bytes after 0x00)
                    if br.remaining_bytes() >= 4:
                        float_bytes = br.read_bytes(4)
                        try:
                            float_val = struct.unpack('<f', float_bytes)[0]
                            # Check if it's a reasonable player count (0-100)
                            if 0 <= float_val <= 100:
                                if in_options_block:
                                    options[key] = int(float_val)
                                else:
                                    parsed_data[key] = int(float_val)
                            else:
                                # Store as raw bytes
                                if in_options_block:
                                    options[key] = float_bytes.hex()
                                else:
                                    parsed_data[key] = float_bytes.hex()
                        except struct.error:
                            pass
                elif value_marker == 0x03:
                    # Boolean value marker (seen with AllowObservers)
                    # Format: key\x00\x03\x01 where \x01 means true, \x00 means false
                    if br.remaining_bytes() >= 1:
                        bool_byte = br.read_byte()
                        bool_val = bool_byte == 0x01
                        if in_options_block:
                            options[key] = bool_val
                        else:
                            parsed_data[key] = bool_val
                else:
                    # Unknown value marker, skip
                    pass
                    
            elif marker == self.BLOCK_START:
                # Start of options block
                in_options_block = True
                
            elif marker == self.BLOCK_END:
                # End of options block
                in_options_block = False
                
            elif marker == 0x00:
                # Null byte, skip
                continue
                
            else:
                # Unknown marker, skip
                continue
        
        # Merge all data - Options block detection might not work perfectly,
        # so we look in both dictionaries
        all_data = {**options, **parsed_data}
        
        # Helper to get value from either dict
        def get_val(key: str, default: Any = None) -> Any:
            return all_data.get(key, default)
        
        # Parse cheats_enabled as boolean
        cheats_str = str(get_val('CheatsEnabled', 'false')).lower()
        cheats_enabled = cheats_str == 'true'
        
        # Parse team_lock
        team_lock = get_val('TeamLock', 'unlocked')
        
        # Get scenario file and extract map info from lookup table
        scenario_file = get_val('ScenarioFile', '')
        max_players, lookup_map_name, map_size = self._extract_map_info(scenario_file)
        
        # Build Status object
        return Status(
            game_name=get_val('GameName', 'Unknown'),
            hosted_by=get_val('HostedBy', 'Unknown'),
            product_code=get_val('ProductCode', 'SC1'),
            scenario_file=scenario_file,
            num_players=int(get_val('PlayerCount', 0)),
            max_players=max_players,
            map_width=map_size[0] if map_size else 0,
            map_height=map_size[1] if map_size else 0,
            map_name_lookup=lookup_map_name or "",
            game_speed=get_val('GameSpeed', 'normal'),
            victory_condition=get_val('Victory', 'demoralization'),
            fog_of_war=get_val('FogOfWar', 'explored'),
            unit_cap=get_val('UnitCap', '500'),
            cheats_enabled=cheats_enabled,
            team_lock=team_lock,
            team_spawn=get_val('TeamSpawn', 'random'),
            allow_observers=get_val('AllowObservers', True),
            no_rush_option=get_val('NoRushOption', 'Off'),
            prebuilt_units=get_val('PrebuiltUnits', 'Off'),
            civilian_alliance=get_val('CivilianAlliance', 'enemy'),
            timeouts=get_val('Timeouts', '3'),
            options=all_data,
            raw={
                'parsed_data': parsed_data,
                'options': options,
                'all_data': all_data,
                'response_length': response_length,
                'raw_hex': data.hex()
            }
        )
    
    # Supreme Commander standard map data
    # Auto-generated from scenario files in /maps folder
    # Format: 'map_id': {'name': 'Map Name', 'players': max_players, 'size': (width, height)}
    # Size units: 256=5km, 512=10km, 1024=20km, 2048=40km, 4096=80km
    SCMP_MAP_DATA = {
        # 2 Player Maps
        'scmp_012': {'name': 'Theta Passage', 'players': 2, 'size': (256, 256)},
        'scmp_013': {'name': 'Winter Duel', 'players': 2, 'size': (256, 256)},
        'scmp_016': {'name': 'Canis River', 'players': 2, 'size': (256, 256)},
        'scmp_019': {'name': 'Finn', 'players': 2, 'size': (512, 512)},
        'scmp_023': {'name': 'Varga Pass', 'players': 2, 'size': (512, 512)},
        # 3 Player Maps
        'scmp_018': {'name': 'Sentry Point', 'players': 3, 'size': (256, 256)},
        'scmp_037': {'name': 'Sludge', 'players': 3, 'size': (256, 256)},
        # 4 Player Maps
        'scmp_003': {'name': 'Drake', 'players': 4, 'size': (1024, 1024)},
        'scmp_004': {'name': 'Emerald Crater', 'players': 4, 'size': (1024, 1024)},
        'scmp_006': {'name': 'Ian', 'players': 4, 'size': (1024, 1024)},
        'scmp_015': {'name': 'Fields of Isis', 'players': 4, 'size': (512, 512)},
        'scmp_017': {'name': 'Syrtis Major', 'players': 4, 'size': (512, 512)},
        'scmp_022': {'name': 'Arctic Refuge', 'players': 4, 'size': (512, 512)},
        'scmp_026': {'name': 'Vya-3 Protectorate', 'players': 4, 'size': (512, 512)},
        'scmp_031': {'name': 'Four-Leaf Clover', 'players': 4, 'size': (512, 512)},
        'scmp_032': {'name': 'The Wilderness', 'players': 4, 'size': (512, 512)},
        'scmp_034': {'name': 'High Noon', 'players': 4, 'size': (512, 512)},
        'scmp_035': {'name': 'Paradise', 'players': 4, 'size': (512, 512)},
        'scmp_036': {'name': 'Blasted Rock', 'players': 4, 'size': (256, 256)},
        'scmp_038': {'name': 'Ambush Pass', 'players': 4, 'size': (256, 256)},
        'scmp_039': {'name': 'Four-Corners', 'players': 4, 'size': (256, 256)},
        # 5 Player Maps
        'scmp_010': {'name': 'Sung Island', 'players': 5, 'size': (1024, 1024)},
        # 6 Player Maps
        'scmp_007': {'name': 'Open Palms', 'players': 6, 'size': (512, 512)},
        'scmp_020': {'name': 'Roanoke Abyss', 'players': 6, 'size': (1024, 1024)},
        'scmp_024': {'name': 'Crossfire Canal', 'players': 6, 'size': (1024, 1024)},
        'scmp_025': {'name': 'Saltrock Colony', 'players': 6, 'size': (512, 512)},
        'scmp_027': {'name': 'The Scar', 'players': 6, 'size': (1024, 1024)},
        'scmp_033': {'name': 'White Fire', 'players': 6, 'size': (512, 512)},
        'scmp_040': {'name': 'The Ditch', 'players': 6, 'size': (1024, 1024)},
        # 7 Player Maps
        'scmp_005': {'name': "Gentleman's Reef", 'players': 7, 'size': (2048, 2048)},
        # 8 Player Maps
        'scmp_001': {'name': 'Burial Mounds', 'players': 8, 'size': (1024, 1024)},
        'scmp_002': {'name': 'Concord Lake', 'players': 8, 'size': (1024, 1024)},
        'scmp_008': {'name': 'Seraphim Glaciers', 'players': 8, 'size': (1024, 1024)},
        'scmp_009': {'name': "Seton's Clutch", 'players': 8, 'size': (1024, 1024)},
        'scmp_011': {'name': 'The Great Void', 'players': 8, 'size': (2048, 2048)},
        'scmp_014': {'name': 'The Bermuda Locket', 'players': 8, 'size': (1024, 1024)},
        'scmp_021': {'name': 'Alpha 7 Quarantine', 'players': 8, 'size': (2048, 2048)},
        'scmp_028': {'name': 'Hanna Oasis', 'players': 8, 'size': (2048, 2048)},
        'scmp_029': {'name': 'Betrayal Ocean', 'players': 8, 'size': (4096, 4096)},
        'scmp_030': {'name': 'Frostmill Ruins', 'players': 8, 'size': (4096, 4096)},
        # Forged Alliance Maps (x1mp_*) - sizes estimated
        'x1mp_001': {'name': 'Loki', 'players': 2, 'size': (256, 256)},
        'x1mp_002': {'name': 'Minerva', 'players': 2, 'size': (256, 256)},
        'x1mp_003': {'name': 'Nowhere', 'players': 2, 'size': (256, 256)},
        'x1mp_004': {'name': 'Sphinx', 'players': 2, 'size': (256, 256)},
        'x1mp_005': {'name': 'Desert', 'players': 4, 'size': (512, 512)},
        'x1mp_006': {'name': 'Eye of the Storm', 'players': 4, 'size': (512, 512)},
        'x1mp_007': {'name': 'Forbidden Pass', 'players': 4, 'size': (512, 512)},
        'x1mp_008': {'name': 'Shards', 'players': 4, 'size': (512, 512)},
        'x1mp_009': {'name': 'Cauldron', 'players': 6, 'size': (1024, 1024)},
        'x1mp_010': {'name': 'Emerald City', 'players': 6, 'size': (1024, 1024)},
        'x1mp_011': {'name': "Finn's Revenge", 'players': 6, 'size': (1024, 1024)},
        'x1mp_012': {'name': 'Flooded Strip Mine', 'players': 6, 'size': (1024, 1024)},
        'x1mp_014': {'name': 'Strip Mine', 'players': 8, 'size': (2048, 2048)},
        'x1mp_017': {'name': 'Setons Clutch II', 'players': 8, 'size': (1024, 1024)},
    }
    
    def _extract_map_info(self, scenario_file: str) -> tuple:
        """
        Extract map information from scenario filename using lookup table.
        
        Supreme Commander does not send max_players, map name, or size in the 
        protocol response, so we use a lookup table for known standard maps.
        
        Args:
            scenario_file: Path to scenario file (e.g., /maps/scmp_039/scmp_039_scenario.lua)
            
        Returns:
            tuple: (max_players, map_name, size) - 0, None, None for unknown maps
                   size is a tuple (width, height) in game units
        """
        if not scenario_file:
            return 0, None, None
        
        # Extract map ID from path (e.g., "scmp_039" from "/maps/scmp_039/scmp_039_scenario.lua")
        import re
        match = re.search(r'(scmp_\d+|x1mp_\d+)', scenario_file.lower())
        if match:
            map_id = match.group(1)
            map_data = self.SCMP_MAP_DATA.get(map_id)
            if map_data:
                return map_data['players'], map_data['name'], map_data.get('size')
        
        return 0, None, None
    
    def _extract_max_players(self, scenario_file: str) -> int:
        """
        Extract maximum players from scenario filename.
        
        Args:
            scenario_file: Path to scenario file
            
        Returns:
            int: Max players for known maps, 0 for unknown maps
        """
        max_players, _ = self._extract_map_info(scenario_file)
        return max_players


if __name__ == "__main__":
    import asyncio
    
    async def main_async():
        print("Supreme Commander Server Discovery")
        print("=" * 50)
        
        # Test direct query to a specific server
        supcom = SupCom(host="172.29.100.29", port=15000, timeout=5.0)
        
        try:
            print(f"\nQuerying server at {supcom._host}:{supcom._port}...")
            status = await supcom.get_status()
            
            print(f"\nServer Status:")
            print(f"  Game Name: {status.game_name}")
            print(f"  Hosted By: {status.hosted_by}")
            print(f"  Product: {status.game_title}")
            print(f"  Map: {status.map_name}")
            print(f"  Players: {status.num_players}/{status.max_players}")
            print(f"  Game Speed: {status.game_speed}")
            print(f"  Victory: {status.victory_condition}")
            print(f"  Unit Cap: {status.unit_cap}")
            print(f"  Cheats: {status.cheats_enabled}")
            print(f"\nFull Options:")
            for key, value in status.options.items():
                print(f"    {key}: {value}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        # Test broadcast discovery
        print("\n" + "=" * 50)
        print("Broadcasting for servers on local network...")
        
        try:
            supcom_broadcast = SupCom(timeout=3.0)
            servers = await supcom_broadcast.discover_servers()
            
            print(f"\nDiscovered {len(servers)} server(s):")
            for ip, server_status in servers:
                print(f"\n  Server at {ip}:")
                print(f"    Game: {server_status.game_name}")
                print(f"    Host: {server_status.hosted_by}")
                print(f"    Players: {server_status.num_players}/{server_status.max_players}")
                
        except Exception as e:
            print(f"Broadcast discovery error: {e}")
    
    asyncio.run(main_async())

