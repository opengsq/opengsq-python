from __future__ import annotations

from opengsq.protocols.gamespy1 import GameSpy1


class SSC(GameSpy1):
    """Serious Sam Classic: The First Encounter Protocol"""

    full_name = "Serious Sam Classic: The First Encounter"

    def __init__(self, host: str, port: int = 25601, timeout: float = 5.0):
        """
        Initialize the Serious Sam Classic protocol.

        :param host: The hostname or IP address of the server.
        :param port: The port number of the server (default: 25601).
        :param timeout: The timeout for the connection in seconds (default: 5.0).
        """
        super().__init__(host, port, timeout)

    async def get_basic(self) -> dict[str, str]:
        """
        Asynchronously retrieves comprehensive information about the game server.

        For Serious Sam Classic, we return the full status information as the basic query.

        :return: A dictionary containing comprehensive server information.
        """
        # Get full status and flatten all information into one dict
        status = await self.get_status()
        
        # Combine info with player information in a flattened format
        result = dict(status.info)
        
        # Add player information as indexed fields
        for i, player in enumerate(status.players):
            for key, value in player.items():
                result[f"{key}_{i}"] = value
        
        return result

    async def get_status(self, xserverquery: bool = False):
        """
        Asynchronously retrieves the status of the game server.

        Serious Sam Classic doesn't support XServerQuery, so we always use the legacy format.

        :param xserverquery: Ignored for Serious Sam Classic (always uses legacy format).
        :return: A Status object containing the status of the game server.
        """
        # Always use legacy format for Serious Sam Classic (no xserverquery)
        return await super().get_status(xserverquery=False)

    async def get_info(self, xserverquery: bool = False) -> dict[str, str]:
        """
        Asynchronously retrieves the information of the current game running on the server.

        :param xserverquery: Ignored for Serious Sam Classic (always uses legacy format).
        :return: A dictionary containing the information of the current game.
        """
        return await super().get_info(xserverquery=False)

    async def get_rules(self, xserverquery: bool = False) -> dict[str, str]:
        """
        Asynchronously retrieves the rules of the current game running on the server.

        :param xserverquery: Ignored for Serious Sam Classic (always uses legacy format).
        :return: A dictionary containing the rules of the current game.
        """
        return await super().get_rules(xserverquery=False)

    async def get_players(self, xserverquery: bool = False) -> list[dict[str, str]]:
        """
        Asynchronously retrieves the information of each player on the server.

        :param xserverquery: Ignored for Serious Sam Classic (always uses legacy format).
        :return: A list containing the information of each player.
        """
        return await super().get_players(xserverquery=False)


if __name__ == "__main__":
    import asyncio

    async def main_async():
        ssc = SSC(host="172.29.100.29", port=25601, timeout=5.0)
        status = await ssc.get_status()
        print(status)

    asyncio.run(main_async())

