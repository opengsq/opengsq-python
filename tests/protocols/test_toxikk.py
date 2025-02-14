import pytest
from opengsq.protocols.toxikk import Toxikk
from ..result_handler import ResultHandler

handler = ResultHandler(__file__)

@pytest.mark.asyncio
async def test_toxikk_status():
    toxikk = Toxikk(host="10.13.37.149", port=14001)
    result = await toxikk.get_status()

    print("\nToxikk Server Details:")
    print(f"Server Name: {result.name}")
    print(f"Map: {result.map}")
    print(f"Game Type: {result.raw.get('gametype')}")
    print(f"Players: {result.num_players}/{result.max_players}")
    print(f"Time Limit: {result.raw.get('time_limit')} minutes")
    print(f"Score Limit: {result.raw.get('frag_limit')} frags")

    print("\nBot Settings:")
    print(f"Bot Count: {result.raw.get('numbots')}")
    print(f"Bot Skill: {result.raw.get('bot_skill')}")
    print(f"VS Bots Mode: {result.raw.get('vs_bots')}")

    print("\nServer Settings:")
    print(f"Password Protected: {'Yes' if result.password_protected else 'No'}")
    print(f"LAN Mode: {'Yes' if result.lan_mode else 'No'}")
    print(f"Stats Enabled: {'Yes' if result.stats_enabled else 'No'}")

    print("\nMutators:")
    mutators = result.raw.get('mutators', [])
    print(", ".join(mutators) if mutators else "None")

    await handler.save_result("test_toxikk_status", result)