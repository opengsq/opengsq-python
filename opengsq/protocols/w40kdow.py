from __future__ import annotations

import asyncio
import struct
import ipaddress
from typing import Optional

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.responses.w40kdow import Status


class W40kDow(ProtocolBase):
    """
    This class represents the Warhammer 40K Dawn of War Protocol.
    It provides methods to listen for broadcast announcements from DoW servers.
    """

    full_name = "Warhammer 40K Dawn of War Protocol"

    def __init__(self, host: str, port: int = 6112, timeout: float = 5.0):
        """
        Initializes the W4kDow object with the given parameters.

        :param host: The host of the server to listen for.
        :param port: The port of the server (default: 6112).
        :param timeout: The timeout for listening to broadcasts.
        """
        super().__init__(host, port, timeout)

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the server status by listening for broadcast announcements.
        
        Dawn of War servers continuously broadcast their status on the network.
        This method listens for these broadcasts and returns the first matching broadcast
        from the specified host.

        :return: A Status object containing the server status.
        :raises InvalidPacketException: If the received packet is invalid.
        :raises asyncio.TimeoutError: If no broadcast is received within the timeout period.
        """
        import socket
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self._port))
        sock.setblocking(False)
        
        loop = asyncio.get_running_loop()
        
        try:
            # Keep receiving broadcasts until we get one from the expected host
            while True:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 2048),
                    timeout=self._timeout
                )
                
                # Only process broadcasts from the expected host
                if addr[0] == self._host:
                    # Parse and return the broadcast data
                    return self._parse_broadcast(data, addr)
        
        finally:
            sock.close()

    def _parse_broadcast(self, data: bytes, addr: tuple) -> Status:
        """
        Parse a Dawn of War server broadcast packet.

        :param data: Raw broadcast data.
        :param addr: Sender address tuple (ip, port).
        :return: Status object with parsed data.
        :raises InvalidPacketException: If the packet is invalid.
        """
        try:
            br = BinaryReader(data)
            
            # Validate header magic (0x08 0x01)
            header = br.read_bytes(2)
            if header != b'\x08\x01':
                raise InvalidPacketException(
                    f"Invalid header. Expected: 0x0801. Received: {header.hex()}"
                )
            
            # Read GUID length and GUID
            guid_len = br.read_long(unsigned=True)
            if guid_len != 38:
                raise InvalidPacketException(
                    f"Unexpected GUID length. Expected: 38. Received: {guid_len}"
                )
            
            guid = br.read_bytes(guid_len).decode('ascii', errors='ignore')
            
            # Read hostname (UTF-16LE with length prefix in code units)
            hostname_len_units = br.read_long(unsigned=True)
            hostname_len_bytes = hostname_len_units * 2
            hostname_bytes = br.read_bytes(hostname_len_bytes)
            hostname = hostname_bytes.decode('utf-16le', errors='ignore')
            
            # Skip null terminator + padding (4 bytes total after hostname)
            br.read_bytes(4)
            
            # Read player counts
            current_players = br.read_long(unsigned=True)
            max_players = br.read_long(unsigned=True)
            
            # Skip unknown flags/status (9 bytes)
            br.read_bytes(9)
            
            # Read IP address (4 bytes, network byte order)
            ip_bytes = br.read_bytes(4)
            ip_address = str(ipaddress.IPv4Address(ip_bytes))
            
            # Validate that the IP in the packet matches the sender's IP
            if ip_address != addr[0]:
                raise InvalidPacketException(
                    f"IP mismatch. Packet IP: {ip_address}, Sender IP: {addr[0]}"
                )
            
            # Read port (2 bytes, little endian)
            port = br.read_short(unsigned=True)
            
            # Skip 4 unknown bytes after port
            br.read_bytes(4)
            
            # Read total payload size (4 bytes) - note: first byte appears twice (redundant)
            br.read_bytes(4)  # Payload size (we don't really need this value)
            br.read_byte()     # Skip the redundant duplicate byte
            
            # Read and validate magic marker "WODW"
            magic_marker = br.read_bytes(4).decode('ascii', errors='ignore')
            if magic_marker != 'WODW':
                raise InvalidPacketException(
                    f"Invalid magic marker. Expected: WODW. Received: {magic_marker}"
                )
            
            # Read build number
            build_number = br.read_long(unsigned=True)
            
            # Read version string
            version_len = br.read_long(unsigned=True)
            version = br.read_bytes(version_len).decode('ascii', errors='ignore')
            
            # Read mod name
            mod_name_len = br.read_long(unsigned=True)
            mod_name = br.read_bytes(mod_name_len).decode('ascii', errors='ignore')
            
            # Read game title (UTF-16LE with length in code units)
            game_title_len_units = br.read_long(unsigned=True)
            game_title_len_bytes = game_title_len_units * 2
            game_title_bytes = br.read_bytes(game_title_len_bytes)
            game_title = game_title_bytes.decode('utf-16le', errors='ignore')
            
            # Read unknown ASCII field (appears to be a version like "1.0", length in bytes)
            unknown_ascii_len = br.read_long(unsigned=True)
            unknown_ascii = br.read_bytes(unknown_ascii_len).decode('ascii', errors='ignore')
            
            # Read map/scenario name (UTF-16LE with length in code units)
            map_scenario_len_units = br.read_long(unsigned=True)
            map_scenario_len_bytes = map_scenario_len_units * 2
            map_scenario_bytes = br.read_bytes(map_scenario_len_bytes)
            map_scenario = map_scenario_bytes.decode('utf-16le', errors='ignore')
            
            # Skip unknown null bytes/padding after map scenario (10 bytes)
            br.read_bytes(10)
            
            # Read number of factions (4 bytes, little endian uint32)
            num_factions = br.read_long(unsigned=True)
            
            # Read faction codes (each is 4 ASCII bytes + 4 padding bytes = 8 bytes total)
            faction_codes = []
            for _ in range(num_factions):
                faction_code = br.read_bytes(4).decode('ascii', errors='ignore')
                br.read_bytes(4)  # Skip 4 padding bytes after each faction code
                faction_codes.append(faction_code)
            
            # Read map features (length-prefixed UTF-16LE strings in code units)
            # Continue reading until we run out of data or hit an invalid length
            map_features = []
            while br.remaining_bytes() >= 4:
                try:
                    feature_len_units = br.read_long(unsigned=True)
                    
                    # Sanity check: length should be reasonable (< 500 characters)
                    if feature_len_units == 0 or feature_len_units > 500:
                        break
                    
                    feature_len_bytes = feature_len_units * 2
                    
                    if br.remaining_bytes() < feature_len_bytes:
                        break
                    
                    feature_bytes = br.read_bytes(feature_len_bytes)
                    feature = feature_bytes.decode('utf-16le', errors='ignore')
                    map_features.append(feature)
                except Exception:
                    # If we can't read a feature, break
                    break
            
            # Create Status object
            status_data = {
                'guid': guid,
                'hostname': hostname,
                'current_players': current_players,
                'max_players': max_players,
                'ip_address': ip_address,
                'port': port,
                'magic_marker': magic_marker,
                'build_number': build_number,
                'version': version,
                'mod_name': mod_name,
                'game_title': game_title,
                'map_scenario': map_scenario,
                'faction_codes': faction_codes,
                'map_features': map_features
            }
            
            return Status(status_data)
            
        except Exception as e:
            if isinstance(e, InvalidPacketException):
                raise
            raise InvalidPacketException(f"Failed to parse broadcast packet: {e}")


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # Test with the provided server
        w4kdow = W40kDow(host="172.29.100.29", port=6112, timeout=10.0)
        
        try:
            print("Listening for Dawn of War server broadcasts...")
            status = await w4kdow.get_status()
            print(f"\n{'='*60}")
            print(f"Server Status:")
            print(f"{'='*60}")
            print(f"GUID: {status.guid}")
            print(f"Hostname: {status.hostname}")
            print(f"Players: {status.current_players}/{status.max_players}")
            print(f"IP:Port: {status.ip_address}:{status.port}")
            print(f"Version: {status.version}")
            print(f"Mod: {status.mod_name} ({status.expansion_name})")
            print(f"Game Title: {status.game_title}")
            print(f"Map/Scenario: {status.map_scenario}")
            print(f"Build: {status.build_number}")
            print(f"Magic: {status.magic_marker}")
            print(f"\nFaction Codes: {', '.join(status.faction_codes)}")
            print(f"\nMap Features:")
            for i, feature in enumerate(status.map_features, 1):
                print(f"  {i}. {feature}")
            
        except asyncio.TimeoutError:
            print("Error: No broadcast received within timeout period")
            print("Make sure a Dawn of War server is running and broadcasting on the network")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main_async())

