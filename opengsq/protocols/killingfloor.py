from opengsq.responses.killingfloor import Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_socket import UdpClient
from opengsq.protocols.unreal2 import Unreal2


class KillingFloor(Unreal2):
    """
    This class represents the Killing Floor Protocol. It provides methods to interact with the Killing Floor API.
    """

    full_name = "Killing Floor Protocol"

    async def get_details(self, strip_color=True) -> Status:
        """
        Asynchronously retrieves the details of the game server.

        Args:
            strip_color (bool, optional): If True, strips color codes from the server name. Defaults to True.

        :return: A Status object containing the details of the game server.
        """
        response = await UdpClient.communicate(
            self, b"\x79\x00\x00\x00" + bytes([self._DETAILS])
        )

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._DETAILS:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(self._DETAILS)
                )
            )

        return Status(
            server_id=br.read_long(),
            server_ip=br.read_string(),
            game_port=br.read_long(),
            query_port=br.read_long(),
            server_name=self._read_string(br, strip_color, False),
            map_name=self._read_string(br, strip_color),
            game_type=self._read_string(br, strip_color),
            num_players=br.read_long(),
            max_players=br.read_long(),
            wave_current=br.read_long(),
            wave_total=br.read_long(),
            ping=br.read_long(),
            flags=br.read_long(),
            skill=self._read_string(br, strip_color),
        )


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # killingfloor
        killingFloor = KillingFloor(host="185.80.128.168", port=7708, timeout=10.0)
        # killingFloor = KillingFloor(host="45.235.99.76", port=7710, timeout=10.0)
        details = await killingFloor.get_details()
        print(details)
        # rules = await killingFloor.get_rules()
        # print(rules)
        # players = await killingFloor.get_players()
        # print(players)

    asyncio.run(main_async())
