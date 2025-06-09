from __future__ import annotations

import os
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.flatout2 import Status


class Flatout2(ProtocolBase):
    """
    This class represents the Flatout 2 Protocol. It provides methods to interact with Flatout 2 game servers.
    The protocol uses broadcast packets to discover and query servers.
    """

    full_name = "Flatout 2 Protocol"
    FLATOUT2_PORT = 23757  # Default broadcast port for Flatout 2

    # Protocol specific constants
    REQUEST_HEADER = b"\x22\x00"
    RESPONSE_HEADERS = [b"\x5f\x00", b"\x55\x00", b"\x59\x00"]  # Multiple valid response headers
    GAME_IDENTIFIER = b"FO14"
    SESSION_ID = b"\x99\x72\xcc\x8f"
    COMMAND_QUERY = b"\x18\x0c"
    PACKET_END = b"\x2e\x55\x19\xb4\xe1\x4f\x81\x4a"

    # Game Mode Identifiers (byte at position -7 from end)
    GAME_MODE_IDENTIFIERS = {
        0x61: "Race",    # Rennen
        0x63: "Derby",   # Derby
        0x65: "Stunt",   # Stunt
    }


    
    # Complete track type mapping (byte at offset 94)
    TRACK_TYPE_NAMES = {
        0x10: "Wald",    # Forest tracks (Timberlands, Pinegrove, City Central, Downtown)
        0x11: "Feld",    # Field tracks (Farmlands, Midwest Ranch, Water Canal, Desert)
        0x12: "Rennen",  # Race tracks (Riverbay Circuit, Motor Raceway, some Farmlands)
        0x13: "Arena",   # Arena tracks (Figure of Eight, Triloop Special, Speedbowl, Sand Speedway, Derby)
        0x14: "Arena",   # Arena tracks (Crash Alley, Speedway variants, Stunt)
        0x15: "Stunt",   # Stunt special tracks
    }
    
    # Combined mapping for precise track identification
    # Key format: (track_type_id, map_id) -> track_name
    PRECISE_TRACK_MAPPING = {
        # Feld tracks with Track Type 0x12
        (0x12, 0x04): "Farmlands 2",
        (0x12, 0x14): "Farmlands 3",
        
        # Kanal tracks with Track Type 0x11
        (0x11, 0x04): "Water Canal 1",
        (0x11, 0x14): "Water Canal 2",
        (0x11, 0x24): "Water Canal 3",
        
        # Wald tracks with Track Type 0x10
        (0x10, 0x14): "Timberlands 1",
        (0x10, 0x24): "Timberlands 2",
        (0x10, 0x34): "Timberlands 3",
        (0x10, 0x44): "Pinegrove 1",
        (0x10, 0x54): "Pinegrove 2",
        (0x10, 0x64): "Pinegrove 3",
        
        # Feld tracks with Track Type 0x11
        (0x11, 0xC4): "Midwest Ranch 1",
        (0x11, 0xD4): "Midwest Ranch 2",
        (0x11, 0xE4): "Midwest Ranch 3",
        (0x11, 0xF4): "Farmlands 1",
        
        # Stadt tracks with Track Type 0x10
        (0x10, 0xA4): "City Central 1",
        (0x10, 0xB4): "City Central 2",
        (0x10, 0xC4): "City Central 3",
        (0x10, 0xD4): "Downtown 1",
        (0x10, 0xE4): "Downtown 2",
        (0x10, 0xF4): "Downtown 3",
        
        # Wüste tracks with Track Type 0x11
        (0x11, 0x64): "Desert Oil Field",
        (0x11, 0x74): "Desert Scrap Yard",
        (0x11, 0x84): "Desert Town",
        
        # Rennen tracks with Track Type 0x12
        (0x12, 0x84): "Riverbay Circuit 1",
        (0x12, 0x94): "Riverbay Circuit 2",
        (0x12, 0xA4): "Riverbay Circuit 3",
        (0x12, 0xB4): "Motor Raceway 1",
        (0x12, 0xC4): "Motor Raceway 2",
        (0x12, 0xD4): "Motor Raceway 3",
        
        # Arena tracks with Track Type 0x13 (Derby and Arena)
        (0x13, 0x46): "Gas Station Derby",
        (0x13, 0x56): "Parking Lot Derby",
        (0x13, 0x66): "Skyscraper Derby",
        (0x13, 0x76): "Derby Bowl 1",
        (0x13, 0x86): "Derby Bowl 2",
        (0x13, 0x96): "Derby Bowl 3",
        (0x13, 0xB4): "Figure of Eight 1",
        (0x13, 0xB6): "Figure of Eight 1",  # Duplicate Map ID
        (0x13, 0xC4): "Triloop Special",
        (0x13, 0xC6): "Triloop Special",    # Duplicate Map ID
        (0x13, 0xD4): "Speedbowl",
        (0x13, 0xD6): "Speedbowl",          # Duplicate Map ID
        (0x13, 0xE4): "Sand Speedway",
        (0x13, 0xE6): "Sand Speedway",      # Duplicate Map ID
        (0x13, 0xF4): "Figure of Eight 2",
        (0x13, 0xF6): "Figure of Eight 2",  # Duplicate Map ID
        
        # Arena tracks with Track Type 0x14 (Speedway and Stunt)
        (0x14, 0x04): "Crash Alley",
        (0x14, 0x06): "Crash Alley",        # Duplicate Map ID
        (0x14, 0x14): "Speedway Left",
        (0x14, 0x16): "Speedway Left",      # Duplicate Map ID
        (0x14, 0x24): "Speedway Right",
        (0x14, 0x26): "Speedway Right",     # Duplicate Map ID
        (0x14, 0x34): "Speedway Special",
        (0x14, 0x36): "Speedway Special",   # Duplicate Map ID
        (0x14, 0x62): "High Jump",
        (0x14, 0x72): "Bowling",
        (0x14, 0x82): "Ski Jump",
        (0x14, 0x92): "Curling",
        (0x14, 0xA2): "Stone Skipping",
        (0x14, 0xB2): "Ring of Fire",
        
        # Stunt special tracks with Track Type 0x15
        (0x15, 0x02): "Field Goal",
        (0x15, 0x12): "Royal Flush",
        (0x15, 0x22): "Basketball",
        (0x15, 0x32): "Darts",
        (0x15, 0x42): "Baseball",
        (0x15, 0x52): "Soccer",
    }

    def __init__(self, host: str, port: int = FLATOUT2_PORT, timeout: float = 5.0):
        """
        Initialize the Flatout 2 protocol handler.

        :param host: The broadcast address (usually '255.255.255.255' for LAN)
        :param port: The port to use (default: 23757)
        :param timeout: Connection timeout in seconds
        """
        if port != self.FLATOUT2_PORT:
            raise ValueError(f"Flatout 2 protocol requires port {self.FLATOUT2_PORT}")
        super().__init__(host, self.FLATOUT2_PORT, timeout)
        self._allow_broadcast = True

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of Flatout 2 servers via broadcast.
        Expects a response packet with server information.

        :return: A Status object containing the status of the game server.
        """
        # Build the request packet
        request_data = (
            self.REQUEST_HEADER +        # Protocol header
            self.SESSION_ID +            # Session ID
            b"\x00" * 4 +               # Padding pre-identifier
            self.GAME_IDENTIFIER +       # "FO14"
            b"\x00" * 8 +               # Padding post-identifier
            self.COMMAND_QUERY +         # Query command
            b"\x00\x00\x22\x00" +       # Command data
            self.PACKET_END              # Standard packet end
        )

        # Send broadcast and receive response
        data = await UdpClient.communicate(self, request_data, source_port=self.FLATOUT2_PORT)



        # Verify response packet
        if not self._verify_packet(data):
            raise InvalidPacketException("Invalid response packet received")

        br = BinaryReader(data)
        return self._parse_response(br, data)

    def _verify_packet(self, data: bytes) -> bool:
        """
        Verifies that a packet is a valid Flatout 2 response.

        :param data: The packet data to verify
        :return: True if the packet is valid, False otherwise
        """
        if len(data) < 14:  # Minimum length for header + session ID + padding + game ID
            return False

        # Check response header - accept any of the valid response headers
        response_header = data[:2]
        header_valid = response_header in self.RESPONSE_HEADERS

        # Check game identifier (position 10-14, after session ID and padding)
        # This is the most reliable indicator for Flatout 2 servers
        game_id = data[10:14]
        game_id_matches = game_id == self.GAME_IDENTIFIER
        if not game_id_matches:
            return False

        return True

    def _read_utf16_string(self, br: BinaryReader) -> str:
        """
        Reads a UTF-16 encoded string from the binary reader.

        :param br: The binary reader to read from
        :return: The decoded string
        """
        bytes_list = []
        while True:
            # Read two bytes at a time (UTF-16)
            char_bytes = br.read_bytes(2)
            if char_bytes == b"\x00\x00":  # End of string
                break
            bytes_list.extend(char_bytes)
        
        return bytes(bytes_list).decode('utf-16-le').strip()

    def _extract_game_mode(self, data: bytes) -> str:
        """
        Extracts the game mode from the payload data.
        Game mode identifier is located at offset -7 (7 bytes from end).

        :param data: The complete response data
        :return: The game mode name or "Unknown" if not found
        """
        try:
            if len(data) >= 7:
                game_mode_id = data[-7]  # 7 bytes from end
                return self.GAME_MODE_IDENTIFIERS.get(game_mode_id, f"Unknown (0x{game_mode_id:02X})")
            else:
                return "Unknown"
        except Exception as e:
            print(f"Error extracting game mode: {e}")
            return "Unknown"

    def _extract_map_name(self, data: bytes, server_name: str) -> str:
        """
        Extracts the map name from the payload data.
        Map ID is located at offset 95 (second-to-last byte).
        Track Type is located at offset 94 (third-to-last byte).

        :param data: The complete response data
        :param server_name: The server name (unused, kept for compatibility)
        :return: The map name or "Unknown Map" if not found
        """
        try:
            # Map ID is at offset 95, Track Type is at offset 94
            if len(data) >= 3:
                track_type_id = data[-3]  # Third-to-last byte (offset 94)
                map_id = data[-2]         # Second-to-last byte (offset 95)
                
                # First try precise mapping using both track type and map ID
                precise_key = (track_type_id, map_id)
                if precise_key in self.PRECISE_TRACK_MAPPING:
                    track_name = self.PRECISE_TRACK_MAPPING[precise_key]
                    track_type_name = self.TRACK_TYPE_NAMES.get(track_type_id, f"Type{track_type_id:02X}")
                    return f"{track_name} ({track_type_name})"
                
                # Fallback to track type name if precise mapping not found
                track_type_name = self.TRACK_TYPE_NAMES.get(track_type_id, f"Type{track_type_id:02X}")
                return f"{track_type_name} Track (ID: 0x{map_id:02X})"
                
            else:
                return "Unknown Map"
                
        except Exception as e:
            print(f"Error extracting map name: {e}")
            return "Unknown Map"

    def _extract_game_limit(self, data: bytes, game_mode: str) -> dict:
        """
        Extracts the game limit from the payload data.
        The limit is encoded in the end byte (offset 96, last byte) and depends on game mode.
        Formula: limit = (end_byte & 0xF0) >> 4

        :param data: The complete response data
        :param game_mode: The game mode (Race, Derby, Stunt)
        :return: Dictionary with limit information or defaults if not found
        """
        try:
            if len(data) >= 1:
                end_byte = data[-1]  # Last byte (offset 96)
                # Extract limit from upper 4 bits
                limit_value = (end_byte & 0xF0) >> 4
                
                if game_mode == "Race":
                    return {
                        "lap_count": limit_value,
                        "time_limit": None,
                        "has_limit": True
                    }
                elif game_mode == "Derby":
                    return {
                        "lap_count": None,
                        "time_limit": limit_value,  # Minutes
                        "has_limit": True
                    }
                elif game_mode == "Stunt":
                    return {
                        "lap_count": None,
                        "time_limit": None,
                        "has_limit": False
                    }
                else:
                    # Unknown game mode, return raw value
                    return {
                        "lap_count": limit_value,
                        "time_limit": None,
                        "has_limit": True
                    }
            else:
                return {
                    "lap_count": None,
                    "time_limit": None,
                    "has_limit": False
                }
        except Exception as e:
            print(f"Error extracting game limit: {e}")
            return {
                "lap_count": None,
                "time_limit": None,
                "has_limit": False
            }

    def _parse_response(self, br: BinaryReader, original_data: bytes) -> Status:
        """
        Parses the binary response into a Status object.
        The response contains UTF-16 encoded strings and various server information.
        Based on payload analysis of Flatout2 protocol responses.

        :param br: BinaryReader containing the response data
        :return: A Status object containing the parsed information
        """
        # Skip header (2), session ID (4), padding (4), game ID (4), padding (8), command (4), data (2), and packet end (8)
        br.read_bytes(36)  # Skip to the server data section

        info = {}

        try:
            # Read server name (UTF-16 encoded)
            server_name = self._read_utf16_string(br)
            info["hostname"] = server_name

            # Extract game mode from the payload
            # Game mode identifier at offset -7
            game_mode = self._extract_game_mode(original_data)
            info["game_mode"] = game_mode

            # Extract map information from the payload
            # Map ID at offset 95, Track Type at offset 94
            map_name = self._extract_map_name(original_data, server_name)
            info["map"] = map_name

            # Extract game limits from the payload
            # Limit is encoded in the end byte (offset 96) and depends on game mode:
            # - Race: lap_count (number of laps)
            # - Derby: time_limit (minutes)
            # - Stunt: no limit (unlimited play time)
            game_limits = self._extract_game_limit(original_data, game_mode)
            info["lap_count"] = game_limits["lap_count"]
            info["time_limit"] = game_limits["time_limit"]
            info["has_limit"] = game_limits["has_limit"]

            # Read server information
            timestamp = br.read_long_long()  # Server timestamp
            info["timestamp"] = str(timestamp)

            server_flags = br.read_long(unsigned=True)  # Server configuration flags
            info["flags"] = str(server_flags)

            # Skip map info and padding to reach player count section
            br.read_bytes(16)  # Skip map info and padding

            # Extract player counts from the correct byte positions
            # The player counts are at fixed positions relative to the end of the payload
            # Max players at -11 bytes from end, Current players at -10 bytes from end
            max_players = 8  # Default
            current_players = 0  # Default
            
            if len(original_data) >= 11:
                max_players_pos = len(original_data) - 11  # 11 bytes from end
                current_players_pos = len(original_data) - 10  # 10 bytes from end
                
                max_players = original_data[max_players_pos]
                current_players_raw = original_data[current_players_pos]
                # Current players are encoded as count * 0x10
                current_players = current_players_raw // 0x10 if current_players_raw > 0 else 0
                
                # Sanity check: current players shouldn't exceed max players
                if current_players > max_players:
                    current_players = max_players
            
            info["current_players"] = current_players
            info["max_players"] = max_players
            
            # Read remaining configuration data
            # Calculate remaining bytes manually since br.tell() doesn't exist
            bytes_read_so_far = 36 + len(server_name.encode('utf-16-le')) + 2 + 8 + 4 + 16  # Approximate
            remaining_bytes = len(original_data) - bytes_read_so_far
            if remaining_bytes > 0 and remaining_bytes < len(original_data):
                try:
                    config_data = br.read_bytes(min(remaining_bytes, 12))
                    info["config"] = config_data.hex()
                except:
                    info["config"] = ""
            else:
                info["config"] = ""

            # Server status (if available in remaining data)
            info["status"] = "1"  # Default active status

        except Exception as e:
            print(f"Error parsing response: {e}")
            # Set defaults on error
            info.setdefault("hostname", "Unknown Server")
            info.setdefault("game_mode", "Unknown")
            info.setdefault("map", "Unknown Map")
            info.setdefault("lap_count", None)
            info.setdefault("time_limit", None)
            info.setdefault("has_limit", False)
            info.setdefault("max_players", 8)
            info.setdefault("current_players", 0)
            info.setdefault("timestamp", "0")
            info.setdefault("flags", "0")
            info.setdefault("status", "1")
            info.setdefault("config", "")

        return Status(info=info)


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # Use broadcast address for LAN discovery
        flatout2 = Flatout2(host="255.255.255.255", port=23757, timeout=5.0)
        status = await flatout2.get_status()
        print(status) 