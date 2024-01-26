from opengsq.responses.raknet import Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class RakNet(ProtocolBase):
    """
    This class represents the RakNet Protocol. It provides methods to interact with the RakNet API.
    (https://wiki.vg/Raknet_Protocol)
    """

    full_name = "RakNet Protocol"

    __ID_UNCONNECTED_PING = b"\x01"
    __ID_UNCONNECTED_PONG = b"\x1C"
    __TIMESTAMP = b"\x12\x23\x34\x45\x56\x67\x78\x89"
    __OFFLINE_MESSAGE_DATA_ID = (
        b"\x00\xFF\xFF\x00\xFE\xFE\xFE\xFE\xFD\xFD\xFD\xFD\x12\x34\x56\x78"
    )
    __CLIENT_GUID = b"\x00\x00\x00\x00\x00\x00\x00\x00"

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        request = (
            self.__ID_UNCONNECTED_PING
            + self.__TIMESTAMP
            + self.__OFFLINE_MESSAGE_DATA_ID
            + self.__CLIENT_GUID
        )
        response = await UdpClient.communicate(self, request)

        br = BinaryReader(response)
        header = br.read_bytes(1)

        if header != self.__ID_UNCONNECTED_PONG:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    header, self.__ID_UNCONNECTED_PONG
                )
            )

        br.read_bytes(
            len(self.__TIMESTAMP) + len(self.__CLIENT_GUID)
        )  # skip timestamp and guid
        magic = br.read_bytes(len(self.__OFFLINE_MESSAGE_DATA_ID))

        if magic != self.__OFFLINE_MESSAGE_DATA_ID:
            raise InvalidPacketException(
                "Magic value mismatch. Received: {}. Expected: {}.".format(
                    magic, self.__OFFLINE_MESSAGE_DATA_ID
                )
            )

        br.read_short()  # skip remaining packet length

        d = [b";"]  # delimiter

        return Status(
            edition=br.read_string(d),
            motd_line1=br.read_string(d),
            protocol_version=int(br.read_string(d)),
            version_name=br.read_string(d),
            num_players=int(br.read_string(d)),
            max_players=int(br.read_string(d)),
            server_unique_id=br.read_string(d),
            motd_line2=br.read_string(d),
            game_mode=br.read_string(d),
            game_mode_numeric=int(br.read_string(d)),
            port_ipv4=int(br.read_string(d)),
            port_ipv6=int(br.read_string(d)),
        )


if __name__ == "__main__":
    import asyncio

    async def main_async():
        raknet = RakNet(host="mc.advancius.net", port=19132, timeout=5.0)
        status = await raknet.get_status()
        print(status)

    asyncio.run(main_async())
