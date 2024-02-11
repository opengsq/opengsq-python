from __future__ import annotations

import aiohttp

from opengsq.responses.kaillera import Status
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Kaillera(ProtocolBase):
    """
    A class used to represent the Kaillera Network Protocol.
    """

    full_name = "Kaillera Network Protocol"

    async def get_status(self) -> bool:
        """
        Checks the status of the server by sending a PING message and expecting a PONG response.

        Returns:
            bool: True if the server responds with PONG, False otherwise.
        """
        response = await UdpClient.communicate(self, b"PING\0")
        return response == b"PONG\x00"

    @staticmethod
    async def query_master_servers() -> list[Status]:
        """
        Queries the master servers for a list of all active servers.

        Returns:
            list[Status]: A list of Status objects representing each server.
        """
        url = "http://www.kaillera.com/raw_server_list2.php"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.text()

        # Format: serverName[LF]ipAddress:port;users/maxusers;gameCount;version;location[LF]
        servers = data.strip().split("\n")
        master_servers = []

        for i in range(0, len(servers), 2):
            server_name, info = servers[i : i + 2]
            items = info.split(";")
            ip_address, port = items[0].split(":")
            users, maxusers = items[1].split("/")
            game_count, version, location = items[2], items[3], items[4]

            master_servers.append(
                Status(
                    server_name,
                    ip_address,
                    int(port),
                    int(users),
                    int(maxusers),
                    int(game_count),
                    version,
                    location,
                )
            )

        return master_servers


if __name__ == "__main__":
    import asyncio

    async def main_async():
        master_servers = await Kaillera.query_master_servers()
        print(master_servers)

        kaillera = Kaillera(host="112.161.44.113", port=27888, timeout=5.0)
        status = await kaillera.get_status()
        print(status)

    asyncio.run(main_async())
