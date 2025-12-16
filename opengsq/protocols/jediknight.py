from __future__ import annotations

import re
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.jediknight import Info, Status, JediKnightStatus
from opengsq.responses.jediknight.status import Player


class JediKnight(ProtocolBase):
    """
    This class represents the Star Wars Jedi Knight - Jedi Academy Protocol.
    It provides methods to interact with Jedi Academy servers.
    """

    full_name = "Star Wars Jedi Knight - Jedi Academy Protocol"

    def __init__(self, host: str, port: int = 29070, timeout: float = 5.0):
        """
        Initializes the JediKnight object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server (default: 29070).
        :param timeout: The timeout for the server connection.
        """
        super().__init__(host, port, timeout)
        self._source_port = 29070  # Jedi Academy requires source port 29070

    async def get_info(self, challenge: str = "xxx") -> Info:
        """
        Asynchronously retrieves the server information.

        :param challenge: The challenge string to send (default: "xxx").
        :return: An Info object containing the server information.
        """
        # Construct the getinfo payload: ffffffff676574696e666f20787878
        payload = b"\xFF\xFF\xFF\xFF" + b"getinfo " + challenge.encode('ascii')

        response_data = await UdpClient.communicate(self, payload, source_port=self._source_port)

        # Parse the response
        br = BinaryReader(response_data)

        # Skip the header (4 bytes of 0xFF)
        header = br.read_bytes(4)
        if header != b"\xFF\xFF\xFF\xFF":
            raise InvalidPacketException(
                f"Invalid packet header. Expected: \\xFF\\xFF\\xFF\\xFF. Received: {header.hex()}"
            )

        # Read the response type
        response_type = br.read_string([b'\n'])
        if response_type != "infoResponse":
            raise InvalidPacketException(
                f"Unexpected response type. Expected: infoResponse. Received: {response_type}"
            )

        # Parse the key-value pairs
        info_data = self._parse_key_value_pairs(br)

        return Info(info_data)

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the server status.

        :return: A Status object containing the server status.
        """
        # Construct the getstatus payload: ffffffff676574737461747573
        payload = b"\xFF\xFF\xFF\xFF" + b"getstatus"

        response_data = await UdpClient.communicate(self, payload, source_port=self._source_port)

        # Parse the response
        br = BinaryReader(response_data)

        # Skip the header (4 bytes of 0xFF)
        header = br.read_bytes(4)
        if header != b"\xFF\xFF\xFF\xFF":
            raise InvalidPacketException(
                f"Invalid packet header. Expected: \\xFF\\xFF\\xFF\\xFF. Received: {header.hex()}"
            )

        # Read the response type
        response_type = br.read_string([b'\n'])
        if response_type != "statusResponse":
            raise InvalidPacketException(
                f"Unexpected response type. Expected: statusResponse. Received: {response_type}"
            )

        # Parse the key-value pairs and players
        status_data, players = self._parse_status_response(br)

        return Status(status_data, players)

    async def get_full_status(self, challenge: str = "xxx") -> JediKnightStatus:
        """
        Asynchronously retrieves both server info and status.

        :param challenge: The challenge string to send (default: "xxx").
        :return: A JediKnightStatus object containing both info and status.
        """
        import asyncio

        # Add a small delay between requests to avoid socket conflicts
        info = await self.get_info(challenge)
        await asyncio.sleep(0.1)  # 100ms delay
        status = await self.get_status()

        return JediKnightStatus(info=info, status=status)

    def _parse_key_value_pairs(self, br: BinaryReader) -> dict[str, str]:
        """
        Parses key-value pairs from the binary reader.
        Jedi Academy uses backslash ( \\ ) as delimiter between keys and values.

        :param br: The BinaryReader object to parse from.
        :return: A dictionary containing the parsed key-value pairs.
        """
        data = {}

        # Read the remaining data as string
        remaining_data = br.read().decode('ascii', errors='ignore')

        # Split by backslash and process pairs
        parts = remaining_data.split('\\')

        # Remove empty first element if it exists (starts with \)
        if parts and parts[0] == '':
            parts = parts[1:]

        # Process pairs (key, value, key, value, ...)
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                key = parts[i].strip()
                value = parts[i + 1].strip()
                if key:  # Only add non-empty keys
                    data[key] = value

        return data

    def _parse_status_response(self, br: BinaryReader) -> tuple[dict[str, str], list[Player]]:
        """
        Parses the status response which contains key-value pairs followed by player info.
        Player info format: score ping "name"

        :param br: The BinaryReader object to parse from.
        :return: A tuple of (status_data dict, players list).
        """
        data = {}
        players = []

        # Read the remaining data as string
        remaining_data = br.read().decode('ascii', errors='ignore')

        # Split by newline to separate server info from player info
        lines = remaining_data.split('\n')

        if lines:
            # First line contains server info (key-value pairs)
            server_info = lines[0]
            parts = server_info.split('\\')

            # Remove empty first element if it exists (starts with \)
            if parts and parts[0] == '':
                parts = parts[1:]

            # Process pairs (key, value, key, value, ...)
            for i in range(0, len(parts) - 1, 2):
                if i + 1 < len(parts):
                    key = parts[i].strip()
                    value = parts[i + 1].strip()
                    if key:  # Only add non-empty keys
                        data[key] = value

            # Parse player lines (format: score ping "name")
            player_pattern = re.compile(r'^(-?\d+)\s+(-?\d+)\s+"([^"]*)"')
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                match = player_pattern.match(line)
                if match:
                    players.append(Player(
                        score=int(match.group(1)),
                        ping=int(match.group(2)),
                        name=match.group(3)
                    ))

        return data, players


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # Test with a Jedi Academy server
        jk = JediKnight(host="127.0.0.1", port=29070, timeout=5.0)

        try:
            print("Getting server info...")
            info = await jk.get_info()
            print(f"Info: {info}")
            print(f"Hostname: {info.hostname}")
            print(f"Map: {info.mapname}")
            print(f"Gametype: {info.gametype} ({info.gametype_translated})")
            print(f"Players: {info.clients}/{info.sv_maxclients}")

            print("\n" + "="*50)
            print("Getting server status...")
            await asyncio.sleep(0.2)  # Wait a bit before next request
            status = await jk.get_status()
            print(f"Status: {status}")
            print(f"Server Name: {status.sv_hostname}")
            print(f"Version: {status.version}")
            print(f"Game: {status.gamename}")
            print(f"Gametype: {status.g_gametype} ({status.g_gametype_translated})")
            print(f"Players ({len(status.players)}):")
            for player in status.players:
                print(f"  - {player.name}: Score={player.score}, Ping={player.ping}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main_async())


