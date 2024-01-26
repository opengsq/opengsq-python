from opengsq.protocols.source import Source


class WON(Source):
    """World Opponent Network (WON) Query Protocol"""

    full_name = "World Opponent Network (WON) Protocol"

    _A2S_INFO = b"details\0"
    _A2S_PLAYER = b"players"
    _A2S_RULES = b"rules"


if __name__ == "__main__":
    import asyncio

    async def main_async():
        won = WON(host="212.227.190.150", port=27020, timeout=5.0)
        info = await won.get_info()
        print(info)
        players = await won.get_players()
        print(players)
        rules = await won.get_rules()
        print(rules)

    asyncio.run(main_async())
