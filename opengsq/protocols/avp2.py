from __future__ import annotations

from opengsq.protocols.gamespy1 import GameSpy1


class AVP2(GameSpy1):
    """Alien vs Predator 2 Protocol (based on GameSpy1)"""

    full_name = "Alien vs Predator 2"

    def __init__(self, host: str, port: int = 27888, timeout: float = 5.0):
        """
        Initialize the AVP2 protocol.

        :param host: The server host address
        :param port: The server port (default: 27888)
        :param timeout: The timeout for the connection (default: 5.0 seconds)
        """
        super().__init__(host, port, timeout)


if __name__ == "__main__":
    import asyncio

    async def main_async():
        avp2 = AVP2(host="172.29.100.29", port=27888, timeout=5.0)
        status = await avp2.get_info()
        print(status)

    asyncio.run(main_async())
