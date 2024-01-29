from __future__ import annotations

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.gamespy2 import Status


class GameSpy3(ProtocolBase):
    """
    This class represents the GameSpy Protocol version 3. It provides methods to interact with the GameSpy API.
    """

    full_name = "GameSpy Protocol version 3"
    challenge_required = False

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server. The status includes information about the server,
        players, and teams.

        :return: A Status object containing the status of the game server.
        """
        # Connect to remote host
        with UdpClient() as udpClient:
            udpClient.settimeout(self._timeout)
            await udpClient.connect((self._host, self._port))

            request_h = b"\xFE\xFD"
            timestamp = b"\x04\x05\x06\x07"
            challenge = b""

            if self.challenge_required:
                # Packet 1: Initial request - (https://wiki.unrealadmin.org/UT3_query_protocol#Packet_1:_Initial_request)
                udpClient.send(request_h + b"\x09" + timestamp)

                # Packet 2: First response - (https://wiki.unrealadmin.org/UT3_query_protocol#Packet_2:_First_response)
                response = await udpClient.recv()

                if response[0] != 9:
                    raise InvalidPacketException(
                        "Packet header mismatch. Received: {}. Expected: {}.".format(
                            chr(response[0]), chr(9)
                        )
                    )

                # Packet 3: Second request - (http://wiki.unrealadmin.org/UT3_query_protocol#Packet_3:_Second_request)
                challenge = int(response[5:].decode("ascii").strip("\x00"))
                challenge = (
                    b"" if challenge == 0 else challenge.to_bytes(4, "big", signed=True)
                )

            request_data = request_h + b"\x00" + timestamp + challenge
            udpClient.send(request_data + b"\xFF\xFF\xFF\x01")

            # Packet 4: Server information response
            # (http://wiki.unrealadmin.org/UT3_query_protocol#Packet_4:_Server_information_response)
            response = await self.__read(udpClient)

        br = BinaryReader(response)

        info = {}

        while True:
            key = br.read_string()

            if key == "":
                break

            info[key] = br.read_string()

        status = Status(
            info,
            self.__get_dictionaries(br, "player"),
            self.__get_dictionaries(br, "team"),
        )

        return status

    async def __read(self, udpClient: UdpClient) -> bytes:
        packet_count = -1
        payloads = {}

        while packet_count == -1 or len(payloads) > packet_count:
            response = await udpClient.recv()

            br = BinaryReader(response)
            header = br.read_byte()

            if header != 0:
                raise InvalidPacketException(
                    "Packet header mismatch. Received: {}. Expected: {}.".format(
                        chr(header), chr(0)
                    )
                )

            # Skip the timestamp and splitnum
            br.read_bytes(13)

            # The 'numPackets' byte
            num_packets = br.read_byte()

            # The low 7 bits are the packet index (starting at zero)
            number = num_packets & 0x7F

            # The high bit is whether or not this is the last packet
            if num_packets & 0x80:
                # Set packet_count if it is the last packet
                packet_count = number + 1

            # The object id
            # 0 = server kv information
            # 1 = player_   \x00\x01player_\x00\x00 since \x01
            # 2 = team_t    \x00\x02team_t\x00\x00  since \x02
            # etc...
            obj_id = br.read_byte()
            header = b""

            if obj_id >= 1:
                # The object key name
                string = br.read_string()

                # How many times did the value appear in the previous packet
                count = br.read_byte()

                # Set back the packet header if it didn't appear before
                header = (
                    b"\x00" + bytes([obj_id]) + string.encode() + b"\x00\x00"
                    if count == 0
                    else b""
                )

            payload = header + br.read()[:-1]

            # Remove the last trash string on the payload
            payloads[number] = payload[: payload.rfind(b"\x00") + 1]

        response = b"".join(payloads[number] for number in sorted(payloads))

        return response

    def __get_dictionaries(
        self, br: BinaryReader, object_type: str
    ) -> list[dict[str, str]]:
        kvs: list[dict[str, str]] = []

        # Return if BaseStream is end
        if br.is_end():
            return kvs

        # Skip a byte
        br.read_byte()

        # Player/Team index
        i = 0

        while not br.is_end():
            key = br.read_string()

            if key:
                # Skip \x00
                br.read_byte()

                # Remove the trailing "_t"
                key = key.rstrip("t").rstrip("_")

                # Change the key to name
                if key == object_type:
                    key = "name"

                while not br.is_end():
                    value = br.read_string().strip()

                    if value:
                        # Add a Dictionary object if not exists
                        if len(kvs) < i + 1:
                            kvs.append({})

                        kvs[i][key] = value
                        i += 1
                    else:
                        break

                i = 0
            else:
                break

        return kvs


if __name__ == "__main__":
    import asyncio

    async def main_async():
        gs3 = GameSpy3(host="95.172.92.116", port=29900, timeout=5.0)
        server = await gs3.get_status()
        print(server)

    asyncio.run(main_async())
