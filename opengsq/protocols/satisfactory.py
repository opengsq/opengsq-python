import struct

from opengsq.responses.satisfactory import Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Satisfactory(ProtocolBase):
    """
    This class represents the Satisfactory Protocol. It provides methods to interact with the Satisfactory API.
    """

    full_name = "Satisfactory Protocol"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server. The status includes the server state, version, and beacon port.
        The server state can be one of the following:
        1 - Idle (no game loaded)
        2 - Currently loading or creating a game
        3 - Currently in game

        :return: A Status object containing the status of the game server.
        """
        # Credit: https://github.com/dopeghoti/SF-Tools/blob/main/Protocol.md

        # Send message id, protocol version
        request = struct.pack("2b", 0, 0) + "opengsq".encode()
        response = await UdpClient.communicate(self, request)
        br = BinaryReader(response)
        header = br.read_byte()

        if header != 1:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(1)
                )
            )

        br.read_byte()  # Protocol version
        br.read_bytes(8)  # Request data

        return Status(
            state=br.read_byte(), version=br.read_long(), beacon_port=br.read_short()
        )


if __name__ == "__main__":
    import asyncio

    async def main_async():
        satisfactory = Satisfactory(host="79.136.0.124", port=15777, timeout=5.0)
        status = await satisfactory.get_status()
        print(status)

    asyncio.run(main_async())
