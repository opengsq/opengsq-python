import struct
import time
import aiohttp

from opengsq.responses.palworld import Status
from opengsq.protocol_base import ProtocolBase


class Palworld(ProtocolBase):
    """
    This class represents the Palworld Protocol. It provides methods to interact with the Palworld REST API.
    """

    full_name = "Palworld Protocol"

    def __init__(self, host: str, port: int, api_username: str, api_password: str, timeout: float = 5):
        """
        Initializes the Palworld object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param api_username: The API username.
        :param api_password: The API password.
        :param timeout: The timeout for the server connection.
        """

        super().__init__(host, port, timeout)

        if api_username is None:
            raise ValueError("api_username must not be None")
        if api_password is None:
            raise ValueError("api_password must not be None")

        self.api_url = f"http://{self._host}:{self._port}/v1/api"
        self.api_username = api_username
        self.api_password = api_password
   
    async def api_request(self,url):
        """
        Asynchronously retrieves data from the game server through the REST API.
        """
        auth = aiohttp.BasicAuth(self.api_username,self.api_password)
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as response:
                data = await response.json()
        return data

    async def get_status(self) -> Status:
        """
        Retrieves the status of the game server. The status includes the server state, name, player count and max player count.
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
            port=8212,
            timeout=5.0,
            api_username="admin",
            api_password="",
        )
        status = await palworld.get_status()
        print(status)

    asyncio.run(main_async())
