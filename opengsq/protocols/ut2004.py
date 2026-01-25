from __future__ import annotations

from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.ut2004 import Info, Player, Rules, Status


class UT2004(ProtocolBase):
    """
    This class represents the Unreal Tournament 2004 Protocol. It provides methods to interact with UT2004 servers.
    """

    full_name = "Unreal Tournament 2004 Protocol"

    def __init__(self, host: str, port: int = 7787, timeout: float = 5.0):
        """
        Initializes the UT2004 object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server (default: 7777 + 10 -> 7787).
        :param timeout: The timeout for the server connection.
        """
        super().__init__(host, port, timeout)

    async def get_info(self) -> Info:
        """
        Asynchronously retrieves the server information.

        :return: A dictionary containing the server information.
        """
        payload = b"\\info\\"
        response_data = await UdpClient.communicate(self, payload)
        return Info(self._parse_key_value_pairs(response_data))

    async def get_players(self) -> list[Player]:
        """
        Asynchronously retrieves the player information.

        :return: A list of Player objects.
        """
        payload = b"\\players\\"
        response_data = await UdpClient.communicate(self, payload)
        data = self._parse_key_value_pairs(response_data)

        # convert <entry>_<num> to a proper player response
        players = []
        i = 0
        while f"player_{i}" in data:
            players.append(
                Player(
                    name=data.get(f"player_{i}", ""),
                    frags=int(data.get(f"frags_{i}", 0)),
                    ping=int(data.get(f"ping_{i}", 0)),
                    team=int(data.get(f"team_{i}", 0)),
                )
            )
            i += 1

        return players

    async def get_rules(self) -> Rules:
        """
        Asynchronously retrieves the server rules.

        :return: A dictionary containing the server rules.
        """
        payload = b"\\rules\\"
        response_data = await UdpClient.communicate(self, payload)
        return Rules(self._parse_key_value_pairs(response_data))

    async def get_full_status(self) -> Status:
        """
        Asynchronously retrieves server info, players, and rules.

        :return: A dictionary containing info, players, and rules.
        """
        import asyncio

        info = await self.get_info()
        await asyncio.sleep(0.1)
        players = await self.get_players()
        await asyncio.sleep(0.1)
        rules = await self.get_rules()

        return {"info": info, "players": players, "rules": rules}

    def _parse_key_value_pairs(self, response_data: bytes) -> dict[str, str]:
        """
        Parses key-value pairs from the response data.
        UT2004 uses backslash ( \\ ) as delimiter between keys and values.

        :param response_data: The raw response bytes to parse.
        :return: A dictionary containing the parsed key-value pairs.
        """
        data = {}

        remaining_data = response_data.decode("utf-8", errors="ignore")
        parts = remaining_data.strip("\\").split("\\")

        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                key = parts[i].strip()
                value = parts[i + 1].strip()
                if key:
                    data[key] = value

        return data


if __name__ == "__main__":
    import asyncio

    async def main_async():
        ut2004 = UT2004(host="37.187.146.47", port=7787, timeout=5.0)

        try:
            print("Getting server info...")
            info = await ut2004.get_info()
            print(info)

            print("\n" + "=" * 50)
            print("Getting player info...")
            await asyncio.sleep(0.1)
            players = await ut2004.get_players()
            print(players)

            print("\n" + "=" * 50)
            print("Getting server rules...")
            await asyncio.sleep(0.1)
            rules = await ut2004.get_rules()
            print(rules)

            print("\n" + "=" * 50)
            print("Getting full status...")
            await asyncio.sleep(0.1)
            full_status = await ut2004.get_full_status()
            print(f"Full Status: {full_status}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(main_async())
