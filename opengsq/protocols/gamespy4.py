from opengsq.protocols import GameSpy3


class GameSpy4(GameSpy3):
    """
    This class represents the GameSpy Protocol version 4. It inherits from the GameSpy3 class and overrides some of its properties.
    """

    full_name = "GameSpy Protocol version 4"
    challenge_required = True


if __name__ == "__main__":
    import asyncio

    async def main_async():
        gs4 = GameSpy4(host="play.avengetech.me", port=19132, timeout=5.0)
        server = await gs4.get_status()
        print(server)

    asyncio.run(main_async())
