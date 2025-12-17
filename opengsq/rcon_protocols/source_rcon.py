import random

from enum import Enum

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import AuthenticationException, InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import TcpClient


class SourceRcon(ProtocolBase):
    """
    This class represents the Source RCON Protocol. It provides methods to interact with the Source RCON API.
    """

    full_name = "Source RCON Protocol"

    def __init__(self, host: str, port: int = 27015, timeout: float = 5.0):
        """
        Initializes the SourceRcon object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param timeout: The timeout for the server connection.
        """
        super().__init__(host, port, timeout)

        self._tcpClient = None

    def __enter__(self):
        """
        Defines what the context manager should do at the beginning of the block created by the with statement.
        Returns the object to be used in the context of the with statement.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Defines what the context manager should do after its block has been executed (or terminates).
        It can suppress exceptions, if needed.
        """
        self.close()

    def close(self):
        """
        Closes the connection to the server.
        """
        if self._tcpClient:
            self._tcpClient.close()

    async def authenticate(self, password: str):
        """
        Asynchronously authenticates the connection to the server using the given password.

        :param password: The password to authenticate with.
        """

        # Connect
        self._tcpClient = TcpClient()
        self._tcpClient.settimeout(self._timeout)
        await self._tcpClient.connect((self._host, self._port))

        # Send password
        id = random.randrange(4096)
        self._tcpClient.send(
            self.__Packet(
                id, self.__PacketType.SERVERDATA_AUTH.value, password
            ).get_bytes()
        )

        # Receive and parse as Packet
        response_data = await self._tcpClient.recv()
        packet = self.__Packet(response_data)

        # Sometimes it will return a PacketType.SERVERDATA_RESPONSE_VALUE, so receive again
        if packet.type != self.__PacketType.SERVERDATA_AUTH_RESPONSE.value:
            response_data = await self._tcpClient.recv()
            packet = self.__Packet(response_data)

        # Throw exception if not PacketType.SERVERDATA_AUTH_RESPONSE
        if packet.type != self.__PacketType.SERVERDATA_AUTH_RESPONSE.value:
            self._tcpClient.close()
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(packet.type),
                    chr(self.__PacketType.SERVERDATA_AUTH_RESPONSE.value),
                )
            )

        # Throw exception if authentication failed
        if packet.id == -1 or packet.id != id:
            self._tcpClient.close()
            raise AuthenticationException("Authentication failed")

    async def send_command(self, command: str) -> str:
        """
        Asynchronously sends a command to the server.

        :param command: The command to send to the server.
        :return: The response from the server.
        """

        # Send the command and a empty command packet
        id = random.randrange(4096)
        dummy_id = id + 1
        self._tcpClient.send(
            self.__Packet(
                id, self.__PacketType.SERVERDATA_EXECCOMMAND.value, command
            ).get_bytes()
        )
        self._tcpClient.send(
            self.__Packet(
                dummy_id, self.__PacketType.SERVERDATA_EXECCOMMAND.value, ""
            ).get_bytes()
        )

        packet_bytes = bytes([])
        response = ""

        while True:
            # Receive
            response_data = await self._tcpClient.recv()

            # Concat to last unused bytes
            packet_bytes += response_data

            # Get the packets and get the unused bytes
            packets, packet_bytes = self.__get_packets(packet_bytes)

            # Loop all packets
            for packet in packets:
                if packet.id == dummy_id:
                    return response

                response += packet.body

    # Handle Multiple-packet Responses
    def __get_packets(self, packet_bytes: bytes):
        """
        Retrieves the packets from the given packet bytes.

        :param packet_bytes: The packet bytes to retrieve packets from.
        :return: A list of packets and any remaining bytes.
        """
        packets: list[SourceRcon.__Packet] = []

        br = BinaryReader(packet_bytes)

        # + 4 to ensure br.ReadInt32() is readable
        while br.stream_position + 4 < len(packet_bytes):
            size = br.read_long()

            if br.stream_position + size > len(packet_bytes):
                return packets, packet_bytes[br.stream_position - 4 :]

            id = br.read_long()
            type = br.read_long()
            body = br.read_string()
            br.read_byte()

            packets.append(self.__Packet(id, type, body))

        return packets, bytes([])

    class __PacketType(Enum):
        SERVERDATA_AUTH = 3
        SERVERDATA_AUTH_RESPONSE = 2
        SERVERDATA_EXECCOMMAND = 2
        SERVERDATA_RESPONSE_VALUE = 0

    class __Packet:
        def __init__(self, *args):
            if len(args) == 3:
                self.id = args[0]
                self.type = args[1]
                self.body = args[2]
            else:
                # Single-packet Responses
                br = BinaryReader(args[0])
                br.read_long()
                self.id = br.read_long()
                self.type = br.read_long()
                self.body = br.read_string()

        def get_bytes(self):
            packet_bytes = self.id.to_bytes(4, byteorder="little")
            packet_bytes += self.type.to_bytes(4, byteorder="little")
            packet_bytes += str.encode(self.body + "\0")
            return len(packet_bytes).to_bytes(4, byteorder="little") + packet_bytes


if __name__ == "__main__":
    import asyncio

    async def main_async():
        with SourceRcon(host="", port=27015, timeout=5.0) as rcon:
            await rcon.authenticate("")
            response = await rcon.send_command("cvarlist")
            print(response)

    asyncio.run(main_async())
