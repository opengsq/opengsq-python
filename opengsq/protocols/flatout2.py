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
    RESPONSE_HEADER = b"\x59\x00"
    GAME_IDENTIFIER = b"FO14"
    SESSION_ID = b"\x99\x72\xcc\x8f"
    COMMAND_QUERY = b"\x18\x0c"
    PACKET_END = b"\x2e\x55\x19\xb4\xe1\x4f\x81\x4a"

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

        # Debug output for packet analysis
        print(f"Response header: {data[:2].hex()}, Expected: {self.RESPONSE_HEADER.hex()}")
        print(f"Session ID: {data[2:6].hex()}")
        print(f"Game ID: {data[10:14]}, Expected: {self.GAME_IDENTIFIER}")
        print(f"Full packet length: {len(data)}")

        # Verify response packet
        if not self._verify_packet(data):
            raise InvalidPacketException("Invalid response packet received")

        br = BinaryReader(data)
        return self._parse_response(br)

    def _verify_packet(self, data: bytes) -> bool:
        """
        Verifies that a packet is a valid Flatout 2 response.

        :param data: The packet data to verify
        :return: True if the packet is valid, False otherwise
        """
        if len(data) < 14:  # Minimum length for header + session ID + padding + game ID
            print(f"Packet too short: {len(data)} bytes")
            return False

        # Check game identifier (position 10-14, after session ID and padding)
        # This is the most reliable indicator for Flatout 2 servers
        game_id = data[10:14]
        game_id_matches = game_id == self.GAME_IDENTIFIER
        if not game_id_matches:
            print(f"Game ID mismatch: got {game_id}, expected {self.GAME_IDENTIFIER}")
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

    def _parse_response(self, br: BinaryReader) -> Status:
        """
        Parses the binary response into a Status object.
        The response contains UTF-16 encoded strings and various server information.

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

            # Read server information
            timestamp = br.read_long_long()  # Server timestamp
            info["timestamp"] = str(timestamp)

            server_flags = br.read_long(unsigned=True)  # Server configuration flags
            info["flags"] = str(server_flags)

            # Skip reserved bytes
            br.read_bytes(8)

            # Read server status
            status_flags = br.read_long(unsigned=True)
            info["status"] = str(status_flags)

            # Read server configuration
            config = br.read_bytes(12)  # Remaining configuration data
            info["config"] = config.hex()

        except Exception as e:
            print(f"Error parsing response: {e}")

        return Status(info=info)


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # Use broadcast address for LAN discovery
        flatout2 = Flatout2(host="255.255.255.255", port=23757, timeout=5.0)
        status = await flatout2.get_status()
        print(status) 