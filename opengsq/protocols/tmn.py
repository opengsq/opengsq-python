from opengsq.protocol_base import ProtocolBase
from opengsq.responses.tmn.status import Status
import asyncio

class TMN(ProtocolBase):
    @property
    def full_name(self) -> str:
        return "Trackmania Nations Forever Protocol"
    
    TMN_PORT = 2350
    
    # TCP packets from documentation
    TCP_PACKET_1 = bytes.fromhex("0e000000820399f895580700000008000000")
    TCP_PACKET_2 = bytes.fromhex("1200000082033bd464400700000007000000d53d4100")
    
    def __init__(self, host: str, port: int = TMN_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)

    async def get_status(self) -> Status:
        """Get server status using direct TCP connection."""
        tcp_data = await self._tcp_info_gathering()
        parsed_data = self._parse_tcp_response(tcp_data)
        return Status(**parsed_data)

    async def _tcp_info_gathering(self) -> bytes:
        """Connect via TCP and gather server information."""
        reader, writer = await asyncio.open_connection(self._host, self._port)
        
        try:
            # Send first TCP packet
            writer.write(self.TCP_PACKET_1)
            await writer.drain()
            
            # Wait 200ms between packets
            await asyncio.sleep(0.2)
            
            # Send second TCP packet
            writer.write(self.TCP_PACKET_2)
            await writer.drain()
            
            # Read response
            response = await reader.read(4096)
            return response
            
        finally:
            writer.close()
            await writer.wait_closed()

    def _parse_tcp_response(self, payload: bytes) -> dict:
        """Parse TCP response to extract server information."""
        # Check if this is a server response (not game client)
        if len(payload) < 100:
            raise Exception("Response too short - likely from game client, not server")
        
        # Extract server information
        server_name = self._extract_server_name(payload)
        max_players = self._extract_max_players(payload)
        current_players_count = self._extract_current_players_count(payload)
        map_name = self._extract_map_name(payload)
        
        # Extract game mode
        game_mode_id = self._extract_game_mode(payload)
        game_mode = self._get_game_mode_name(game_mode_id)
        
        result = {
            'name': server_name,
            'map': map_name,
            'game_type': game_mode,
            'num_players': current_players_count,
            'max_players': max_players,
            'password_protected': False,  # Not available in this protocol
        }
        
        return result

    def _extract_server_name(self, payload: bytes) -> str:
        """Extract server name from TCP payload."""
        try:
            # Server name comes after #SRV# marker
            srv_marker = b'#SRV#'
            idx = payload.find(srv_marker)
            
            if idx == -1:
                return "Unknown"
            
            # Look for the server name after the #SRV# structure
            search_start = idx + len(srv_marker) + 10
            
            # Find potential server name by looking for readable ASCII sequences
            for i in range(search_start, min(len(payload), search_start + 200)):
                if payload[i] >= 32 and payload[i] <= 126:  # Printable ASCII
                    name_start = i
                    name_end = name_start
                    
                    # Find end of name (stop at non-printable or null)
                    while (name_end < len(payload) and 
                           payload[name_end] >= 32 and 
                           payload[name_end] <= 126):
                        name_end += 1
                    
                    # If we found a reasonable length name (3+ chars)
                    if name_end - name_start >= 3:
                        name_bytes = payload[name_start:name_end]
                        name = name_bytes.decode('utf-8', errors='ignore').strip()
                        if name and len(name) >= 3:  # Valid server name
                            # Check if the next bytes indicate structure vs continued name
                            next_bytes = payload[name_end:name_end+4] if name_end+4 <= len(payload) else payload[name_end:]
                            last_char = name[-1]
                            
                            # Check pattern: if next bytes start with specific patterns,
                            # the last character might be structure data misread as text
                            needs_correction = False
                            if len(next_bytes) >= 2:
                                # Pattern 1: 01 04 (original detection)
                                if next_bytes[0] == 0x01 and next_bytes[1] == 0x04:
                                    needs_correction = True
                                # Pattern 2: 01 09 (new pattern seen in "Organich")  
                                elif next_bytes[0] == 0x01 and next_bytes[1] == 0x09:
                                    needs_correction = True
                                # Pattern 3: Check if last char is 0x68 ('h') and followed by 01
                                elif last_char == 'h' and next_bytes[0] == 0x01:
                                    needs_correction = True
                            
                            if needs_correction and len(name) > 1:
                                corrected_name = name[:-1] 
                                return corrected_name
                            else:
                                return name
            
            return "Unknown"
        except Exception as e:
            return "Unknown"

    def _extract_max_players(self, payload: bytes) -> int:
        """Extract maximum player count from TCP payload."""
        try:
            srv_marker = b'#SRV#'
            idx = payload.find(srv_marker)
            
            if idx != -1:
                # Check position +9 first (seems to be max players for .25 servers)
                if len(payload) > idx + 9:
                    value_9 = payload[idx + 9]
                    if len(payload) > idx + 10:
                        value_10 = payload[idx + 10]
                        
                        # If +9 is small and +10 is larger, then +9 might be current players and +10 might be max players
                        if value_9 <= 5 and value_9 > 0 and value_10 > value_9:
                            return value_10
                        
                        # Original logic for no-players case (when +9 is the max players)
                        if value_9 >= 5 and value_9 <= 32:  # Reasonable max player range
                            return value_9
                
                # Check position +11 (might be max players for .29 servers)
                if len(payload) > idx + 11:
                    value_11 = payload[idx + 11]
                    if value_11 >= 5 and value_11 <= 32:  # Reasonable max player range
                        return value_11
                
                # Fallback to original position
                original_value = payload[idx + 10] if len(payload) > idx + 10 else 0
                return original_value
            
            return 0
        except Exception as e:
            return 0

    def _extract_current_players_count(self, payload: bytes) -> int:
        """Extract current player count from TCP payload (position +10 after #SRV#)."""
        try:
            srv_marker = b'#SRV#'
            idx = payload.find(srv_marker)
            
            if idx != -1:
                # Logic: If we see pattern like +9=2, +10=5, then +9 is likely current players
                if len(payload) > idx + 10:
                    value_9 = payload[idx + 9] if len(payload) > idx + 9 else 0
                    value_10 = payload[idx + 10]
                    
                    # If +9 is a small number (like 2) and +10 is larger (like 5),
                    # then +9 is likely the current player count
                    if value_9 > 0 and value_9 <= 5 and value_10 > value_9:
                        return value_9
                    else:
                        return value_10
                
                # Fallback to original position
                if len(payload) > idx + 10:
                    current_count = payload[idx + 10]
                    return current_count
            
            return 0
        except Exception as e:
            return 0

    def _extract_map_name(self, payload: bytes) -> str:
        """Extract map name from TCP payload."""
        try:
            # Method 1: Look for common map patterns like A01-Race, A02-Race, etc.
            import re
            
            # Convert hex to ASCII and look for map patterns
            try:
                ascii_parts = []
                for i in range(0, len(payload), 1):
                    if payload[i] >= 0x20 and payload[i] <= 0x7E:  # Printable ASCII
                        ascii_parts.append(chr(payload[i]))
                    else:
                        ascii_parts.append(' ')
                
                ascii_string = ''.join(ascii_parts)
                
                # Look for patterns like A01-Race, A02-Race, etc.
                map_patterns = [
                    r'A\d{2}-Race',
                    r'B\d{2}-Race', 
                    r'C\d{2}-[A-Za-z]+',
                    r'A\d{2}-[A-Za-z]+',
                    r'[A-Z]\d{2}-[A-Za-z]+',
                ]
                
                for pattern in map_patterns:
                    matches = re.findall(pattern, ascii_string)
                    if matches:
                        map_name = matches[0]
                        
                        # Apply same 'h' correction as for server names
                        # Check if map name ends with 'h' that might be a structure byte (0x68)
                        if map_name.endswith('h') and len(map_name) > 5:
                            # For map names like "C04-Raceh" -> "C04-Race"
                            corrected_name = map_name[:-1]
                            # Validate that the corrected name still makes sense
                            if corrected_name.endswith('Race') or corrected_name.endswith('Speed') or corrected_name.endswith('Rally'):
                                return corrected_name
                        
                        return map_name
                
            except Exception as e:
                pass
            
            # Method 2: Direct byte search for known map names
            map_candidates = [b'A01-Race', b'A02-Race', b'A03-Race', b'A04-Race', b'A05-Race',
                            b'B01-Race', b'B02-Race', b'B03-Race', b'B04-Race', b'B05-Race',
                            b'C01-Race', b'C02-Race', b'C03-Race', b'C04-Race', b'C05-Race']
            
            for candidate in map_candidates:
                pos = payload.find(candidate)
                if pos != -1:
                    map_name = candidate.decode('utf-8')
                    return map_name
            
            # Method 3: Look for any reasonable ASCII string that might be a map name
            i = 0
            while i < len(payload) - 5:
                if (payload[i] in [ord('A'), ord('B'), ord('C')] and 
                    payload[i+1] >= ord('0') and payload[i+1] <= ord('9') and
                    payload[i+2] >= ord('0') and payload[i+2] <= ord('9') and
                    payload[i+3] == ord('-')):
                    
                    # Found potential map name start
                    name_start = i
                    name_end = i + 4  # Start after "AXX-"
                    
                    # Read until non-ASCII or reasonable end
                    while (name_end < len(payload) and 
                           payload[name_end] >= 0x20 and payload[name_end] <= 0x7E and
                           name_end - name_start < 20):  # Max 20 chars
                        name_end += 1
                    
                    if name_end - name_start >= 5:  # At least "A01-X"
                        potential_map = payload[name_start:name_end].decode('utf-8', errors='ignore')
                        # Basic validation
                        if '-' in potential_map and len(potential_map) >= 5:
                            return potential_map
                
                i += 1
            
            return "Unknown"
            
        except Exception as e:
            return "Unknown"

    def _extract_game_mode(self, payload: bytes) -> int:
        """Extract game mode ID from TCP payload."""
        try:
            # Method 1: Search for the standard pattern with FF FF FF FF marker
            marker = b'\xff\xff\xff\xff'
            idx = payload.find(marker)
            
            if idx != -1 and len(payload) > idx + 7:
                # Check the pattern type and extract game mode at offset +7
                pattern_type = payload[idx + 4] if len(payload) > idx + 4 else 0
                game_mode_id = payload[idx + 7]
                return game_mode_id
            
            # Method 2: Alternative patterns for .25 servers that don't use FF FF FF FF
            # Look for "Stadium" and check the pattern after it
            stadium_pos = payload.find(b'Stadium')
            if stadium_pos != -1:
                # Look for patterns after Stadium
                pattern_start = stadium_pos + len(b'Stadium')
                if len(payload) > pattern_start + 10:
                    # Check for specific byte patterns that indicate game modes
                    # Pattern analysis from debug data:
                    pattern_area = payload[pattern_start:pattern_start + 10]
                    
                    # Check specific positions for game mode indicators
                    if len(pattern_area) >= 7:
                        key_byte_1 = pattern_area[5] if len(pattern_area) > 5 else 0
                        key_byte_2 = pattern_area[6] if len(pattern_area) > 6 else 0
                        
                        # Known patterns for .25 servers:
                        if key_byte_1 == 0x01 and key_byte_2 == 0x20:  # 01 20
                            return 0  # Time Attack
                        elif key_byte_1 == 0x03 and key_byte_2 == 0x1e:  # 03 1e
                            return 3  # Tournament
                        elif key_byte_1 == 0x06 and key_byte_2 == 0x32:  # 06 32
                            return 6  # Team
                        elif key_byte_1 == 0x07 and key_byte_2 == 0x03:  # 07 03
                            return 7  # Rounds
                        elif key_byte_1 == 0x09:  # 09 XX
                            return 9  # Cup
            
            # Fallback: return 0 (Time Attack) as default
            return 0
        except Exception as e:
            return 0

    def _get_game_mode_name(self, mode_id: int) -> str:
        """Convert game mode ID to human readable name."""
        mode_names = {
            0: "Time Attack",
            3: "Tournament", 
            6: "Team",
            7: "Rounds",
            9: "Cup"
        }
        return mode_names.get(mode_id, "Unknown") 