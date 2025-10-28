from __future__ import annotations

from opengsq.protocols.gamespy2 import GameSpy2


class Halo1(GameSpy2):
    """Halo 1 Multiplayer Protocol (based on GameSpy2)"""

    full_name = "Halo 1 Multiplayer"

    def __init__(self, host: str, port: int = 2302, timeout: float = 5.0):
        """
        Initialize the Halo 1 protocol.

        :param host: The server host address
        :param port: The server port (default: 2302)
        :param timeout: The timeout for the connection (default: 5.0 seconds)
        """
        super().__init__(host, port, timeout)


if __name__ == "__main__":
    import asyncio

    async def main_async():
        halo1 = Halo1(host="172.29.100.29", port=2302, timeout=5.0)
        status = await halo1.get_status()
        print(status)

    asyncio.run(main_async())
