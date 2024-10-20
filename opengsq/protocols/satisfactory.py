import struct
import time
import aiohttp

from opengsq.responses.satisfactory import Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Satisfactory(ProtocolBase):
    """
    This class represents the Satisfactory Protocol. It provides methods to interact with the Satisfactory Lightweight Query API.
    """

    full_name = "Satisfactory Protocol"

    def __init__(self, host: str, port: int, app_token: str, timeout: float = 5):
        """
        Initializes the Satisfactory object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param access_token: The application token for the Satisfactory dedicated server.
        :param timeout: The timeout for the server connection.
        """

        super().__init__(host, port, timeout)

        if app_token is None:
            raise ValueError("app_token must not be None")

        self.api_url = f"https://{self._host}:{self._port}/api/v1/"
        self.app_token = app_token
        self.protocol_magic = 0xF6D5
        self.protocol_version = 1

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server. The status includes the server state, name, player count and max player count.
        The server state can be one of the following:
        0 - Offline (The server is offline. Servers will never send this as a response)
        1 - Idle (The server is running, but no save is currently loaded)
        2 - Loading (The server is currently loading a map. In this state, HTTPS API is unavailable)
        3 - Playing (The server is running, and a save is loaded. Server is joinable by players)

        :return: A Status object containing the status of the game server.
        """

        # Generate a unique cookie using the current time (in ticks)
        cookie = int(time.time() * 1000)

        # Construct the request packet
        request = struct.pack(
            "<HBBQb", self.protocol_magic, 0, self.protocol_version, cookie, 1
        )

        # Send the Poll Server State request
        response = await UdpClient.communicate(self, request)

        # Unpack the response message
        (
            protocol_magic,
            _,
            _,
            received_cookie,
            server_state,
            server_netcl,
            server_flags,
            num_substates,
        ) = struct.unpack("<HBBQBLQB", response[:26])

        if protocol_magic != self.protocol_magic or received_cookie != cookie:
            return None

        # Extract server name length and server name
        server_name_length = struct.unpack(
            "<H", response[26 + (num_substates * 3) : 28 + (num_substates * 3)]
        )[0]
        server_name = response[
            28 + (num_substates * 3) : 28 + (num_substates * 3) + server_name_length
        ].decode("utf-8")

        # Request max number of players and number of players
        if server_state == 3:

            headers = {
                "Authorization": f"Bearer {self.app_token}",
                "Content-Type": "application/json",
            }

            data = {"function": "QueryServerState", "data": {"ServerGameState": {}}}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=data,
                    headers=headers,
                    ssl=False,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            server_max_nb_players, server_cur_nb_players = data.get("data", {}).get(
                "serverGameState", {}
            ).get("playerLimit", "Not Available"), data.get("data", {}).get(
                "serverGameState", {}
            ).get(
                "numConnectedPlayers", "Not Available"
            )

        else:
            server_max_nb_players, server_cur_nb_players = 0, 0

        return Status(
            state=server_state,
            name=server_name,
            num_players=server_cur_nb_players,
            max_players=server_max_nb_players,
        )


if __name__ == "__main__":
    import asyncio

    async def main_async():
        satisfactory = Satisfactory(
            host="79.136.0.124",
            port=7777,
            timeout=5.0,
            app_token="ewoJInBsIjogIkFQSVRva2VuIgp9.EE80F05DAFE991AE8850CD4CFA55840D9F41705952A96AF054561ABA3676BE4D4893B162271D3BC0A0CC50797219D2C8E627F0737FC8776F3468EA44B3700EF7",
        )
        status = await satisfactory.get_status()
        print(status)

    asyncio.run(main_async())
