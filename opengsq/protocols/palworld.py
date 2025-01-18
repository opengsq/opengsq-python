import struct
import time
import aiohttp

from opengsq.responses.palworld import Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Palworld(ProtocolBase):
    """
    This class represents the Palworld Protocol. It provides methods to interact with the Palworld Rest API.
    """

    full_name = "Palworld Protocol"

    def __init__(self, host: str, port: int, app_username: str, app_password: str, timeout: float = 5):
        """
        Initializes the Palworld object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param app_username: The application username.
        :param app_password: The application password.
        :param timeout: The timeout for the server connection.
        """

        super().__init__(host, port, timeout)

        if app_username is None:
            raise ValueError("app_username must not be None")
        if app_password is None:
            raise ValueError("app_password must not be None")

        self.api_url = f"http://{self._host}:{self._port}/v1/api"
        self.app_username = app_username
        self.app_password = app_password
   
    async def api_request(self,url):
        auth = aiohttp.BasicAuth(self.app_username,self.app_password)
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as response:
                data = await response.json()
        return data

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server. The status includes the server state, name, player count and max player count.
        """
        info_data = await self.api_request(f"{self.api_url}/info")
        metrics_data = await self.api_request(f"{self.api_url}/metrics")

        server_name = info_data["servername"]
        server_cur_players = metrics_data["currentplayernum"]
        server_max_players = metrics_data["maxplayernum"]

        return Status(
            server_name=server_name,
            num_players=server_cur_players,
            max_players=server_max_players,
        )


if __name__ == "__main__":
    import asyncio

    async def main_async():
        palworld = Palworld(
            host="79.136.0.124",
            port=8123,
            timeout=5.0,
            app_username="default",
            app_password="default",
        )
        status = await palworld.get_status()
        print(status)

    asyncio.run(main_async())
