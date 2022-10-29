from opengsq.protocols.source import Source


class WON(Source):
    """World Opponent Network (WON) Query Protocol"""
    full_name = 'World Opponent Network (WON) Protocol'

    _A2S_INFO = b'details\0'
    _A2S_PLAYER = b'players'
    _A2S_RULES = b'rules'


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        won = WON(address='212.227.190.150', query_port=27020, timeout=5.0)
        info = await won.get_info()
        players = await won.get_players()
        rules = await won.get_rules()
        print(json.dumps(info, indent=None, ensure_ascii=False) + '\n')
        print(json.dumps(players, indent=None, ensure_ascii=False) + '\n')
        print(json.dumps(rules, indent=None, ensure_ascii=False) + '\n')

    asyncio.run(main_async())
