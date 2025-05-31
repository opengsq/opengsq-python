from __future__ import annotations

from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.binary_reader import BinaryReader
from opengsq.responses.warcraft3 import Status, Player

class Warcraft3(ProtocolBase):
    """
    This class represents the Warcraft 3 Protocol. It provides methods to interact with Warcraft 3 game servers.
    """

    full_name = "Warcraft 3 Protocol"
    WARCRAFT3_PORT = 6112  # Default port for Warcraft 3

    # Protocol specific constants
    _REQUEST_HEADER = bytes.fromhex("f7 2f 10 00 50 58 33 57")
    _RESPONSE_HEADER = bytes.fromhex("f7 30")

    def __init__(self, host: str, port: int = WARCRAFT3_PORT, timeout: float = 5.0):
        """
        Initialize the Warcraft 3 protocol handler.

        :param host: The server address
        :param port: The port to use (default: 6112)
        :param timeout: Connection timeout in seconds
        """
        if port != self.WARCRAFT3_PORT:
            raise ValueError(f"Warcraft 3 protocol requires port {self.WARCRAFT3_PORT}")
        super().__init__(host, self.WARCRAFT3_PORT, timeout)

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        # Create the full request packet
        request = self._REQUEST_HEADER + bytes.fromhex("1a 00 00 00 00 00 00 00")
        
        # Send request and receive response
        response = await UdpClient.communicate(self, request)

        # Validate response header
        if not response.startswith(self._RESPONSE_HEADER):
            raise Exception("Invalid response header")

        # Parse the response using BinaryReader
        br = BinaryReader(response[2:])  # Skip the header bytes

        # Read response size
        response_size = br.read_bytes(2)  # 8A 00
        
        # Read protocol identifier
        protocol_id = br.read_bytes(8)  # 50 58 33 57 1A 00 00 00
        
        # Read game version
        game_version = br.read_bytes(4)  # 01 00 00 00
        
        # Read server info
        server_info = br.read_bytes(4)  # 94 3E 02 00
        
        # Read hostname (null-terminated string)
        hostname = ""
        while True:
            byte = br.read_bytes(1)
            if byte == b'\x00':
                break
            hostname += byte.decode('latin1')
            
        # Store raw data for debugging
        raw = {
            'response_size': response_size.hex(),
            'protocol_id': protocol_id.hex(),
            'game_version': game_version.hex(),
            'server_info': server_info.hex(),
            'remaining_data': br.read_bytes(br.remaining_bytes()).hex()
        }
        
        return Status(
            game_version=game_version.hex(),
            hostname=hostname,
            map_name="Unknown",  # TODO: Parse from remaining data
            game_type="Unknown",  # TODO: Parse from remaining data
            num_players=0,  # TODO: Parse from remaining data
            max_players=12,  # Default max players in WC3
            players=[],  # TODO: Parse from remaining data
            raw=raw
        ) 