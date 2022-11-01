from opengsq.protocols import GameSpy3


class GameSpy4(GameSpy3):
    """GameSpy Protocol version 4"""
    full_name = 'GameSpy Protocol version 4'
    challenge = True


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs4 = GameSpy4(address='188.18.10.72', query_port=19133, timeout=5.0)
        server = await gs4.get_status()
        print(json.dumps(server, indent=None))

    asyncio.run(main_async())
