from __future__ import annotations

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.cod1 import Info, Status, Cod1Status


class CoD1(ProtocolBase):
    """
    This class represents the Call of Duty 1 Protocol. It provides methods to interact with CoD1 servers.
    """

    full_name = "Call of Duty 1 Protocol"

    def __init__(self, host: str, port: int = 28960, timeout: float = 5.0):
        """
        Initializes the CoD1 object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server (default: 28960).
        :param timeout: The timeout for the server connection.
        """
        super().__init__(host, port, timeout)
        self._source_port = 28960  # CoD1 requires source port 28960

    async def get_info(self, challenge: str = "xxx") -> Info:
        """
        Asynchronously retrieves the server information.

        :param challenge: The challenge string to send (default: "xxx").
        :return: An Info object containing the server information.
        """
        # Construct the getinfo payload: ffffffff676574696e666f20787878
        payload = b"\xff\xff\xff\xff" + b"getinfo " + challenge.encode("ascii")

        response_data = await UdpClient.communicate(
            self, payload, source_port=self._source_port
        )

        # Parse the response
        br = BinaryReader(response_data)

        # Skip the header (4 bytes of 0xFF)
        header = br.read_bytes(4)
        if header != b"\xff\xff\xff\xff":
            raise InvalidPacketException(
                f"Invalid packet header. Expected: \\xFF\\xFF\\xFF\\xFF. Received: {header.hex()}"
            )

        # Read the response type
        response_type = br.read_string([b"\n"])
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
        payload = b"\xff\xff\xff\xff" + b"getstatus"

        response_data = await UdpClient.communicate(
            self, payload, source_port=self._source_port
        )

        # Parse the response
        br = BinaryReader(response_data)

        # Skip the header (4 bytes of 0xFF)
        header = br.read_bytes(4)
        if header != b"\xff\xff\xff\xff":
            raise InvalidPacketException(
                f"Invalid packet header. Expected: \\xFF\\xFF\\xFF\\xFF. Received: {header.hex()}"
            )

        # Read the response type
        response_type = br.read_string([b"\n"])
        if response_type != "statusResponse":
            raise InvalidPacketException(
                f"Unexpected response type. Expected: statusResponse. Received: {response_type}"
            )

        # Parse the key-value pairs
        status_data = self._parse_key_value_pairs(br)

        return Status(status_data)

    async def get_full_status(self, challenge: str = "xxx") -> Cod1Status:
        """
        Asynchronously retrieves both server info and status.

        :param challenge: The challenge string to send (default: "xxx").
        :return: A Cod1Status object containing both info and status.
        """
        import asyncio

        # Add a small delay between requests to avoid socket conflicts
        info = await self.get_info(challenge)
        await asyncio.sleep(0.1)  # 100ms delay
        status = await self.get_status()

        return Cod1Status(info=info, status=status)

    def _parse_key_value_pairs(self, br: BinaryReader) -> dict[str, str]:
        """
        Parses key-value pairs from the binary reader.
        CoD1 uses backslash ( \\ ) as delimiter between keys and values.

        :param br: The BinaryReader object to parse from.
        :return: A dictionary containing the parsed key-value pairs.
        """
        data = {}

        # Read the remaining data as string
        remaining_data = br.read().decode("ascii", errors="ignore")

        # Split by backslash and process pairs
        parts = remaining_data.split("\\")

        # Remove empty first element if it exists (starts with \)
        if parts and parts[0] == "":
            parts = parts[1:]

        # Process pairs (key, value, key, value, ...)
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                key = parts[i].strip()
                value = parts[i + 1].strip()
                if key:  # Only add non-empty keys
                    data[key] = value

        return data


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # Test with the provided server
        cod1 = CoD1(host="172.29.100.29", port=28960, timeout=5.0)

        try:
            print("Getting server info...")
            info = await cod1.get_info()
            print(f"Info: {info}")
            print(f"Hostname: {info.hostname}")
            print(f"Map: {info.mapname}")
            print(f"Gametype: {info.gametype}")
            print(f"Players: {info.clients}/{info.sv_maxclients}")

            print("\n" + "=" * 50)
            print("Getting server status...")
            await asyncio.sleep(0.2)  # Wait a bit before next request
            status = await cod1.get_status()
            print(f"Status: {status}")
            print(f"Server Name: {status.sv_hostname}")
            print(f"Version: {status.version}")
            print(f"Game: {status.gamename}")
            print(f"Uptime: {status.uptime}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(main_async())
