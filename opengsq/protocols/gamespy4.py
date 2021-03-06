from opengsq.protocols import GameSpy3


class GameSpy4(GameSpy3):
    """GameSpy Query Protocol version 4"""
    full_name = 'GameSpy Query Protocol version 4'
    challenge = True
    
    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        """GameSpy Query Protocol version 4"""
        super().__init__(address, query_port, timeout)

if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs4 = GameSpy4(address='188.18.10.72', query_port=19133, timeout=5.0)
        server = await gs4.get_status()
        print(json.dumps(server, indent=None))

    asyncio.run(main_async())
