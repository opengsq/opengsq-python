from __future__ import annotations

from typing import Any
import aiohttp
import time

from opengsq.protocol_base import ProtocolBase


class FiveM(ProtocolBase):
    """
    This class represents the FiveM Protocol (https://docs.fivem.net/docs/server-manual/proxy-setup/). It provides methods to interact with the FiveM API.
    """

    full_name = "FiveM Protocol"

    async def _get(self, filename: str) -> dict[str, Any]:
        """
        Asynchronously retrieves the JSON data from the given filename on the server.

        :param filename: The filename to retrieve data from.
        :return: A dictionary containing the JSON data.
        """
        url = f"http://{self._host}:{self._port}/{filename}.json?v={int(time.time())}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json(content_type=None)

    async def get_info(self) -> dict[str, Any]:
        """
        Asynchronously retrieves the information of the game server.

        :return: A dictionary containing the information of the game server.
        """
        return await self._get("info")

    async def get_players(self) -> list[dict[str, Any]]:
        """
        Asynchronously retrieves the list of players on the game server.

        :return: A list of players on the game server.
        """
        return await self._get("players")

    async def get_dynamic(self) -> dict[str, Any]:
        """
        Asynchronously retrieves the dynamic data of the game server.

        :return: A dictionary containing the dynamic data of the game server.
        """
        return await self._get("dynamic")


if __name__ == "__main__":
    import asyncio

    async def main_async():
        fivem = FiveM(host="144.217.10.12", port=30120, timeout=5.0)
        info = await fivem.get_info()
        print(info)
        players = await fivem.get_players()
        print(players)
        dynamic = await fivem.get_dynamic()
        print(dynamic)

    asyncio.run(main_async())
