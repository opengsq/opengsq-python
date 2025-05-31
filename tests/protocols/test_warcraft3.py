import pytest
from opengsq.protocols.warcraft3 import Warcraft3
from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

@pytest.mark.asyncio
async def test_warcraft3_status():
    warcraft3 = Warcraft3(host="10.10.101.4", port=6112)  # Replace with your test server
    result = await warcraft3.get_status()

    print("\nWarcraft 3 Server Details:")
    print(f"Server Name: {result.hostname}")
    print(f"Game Version: {result.game_version}")
    print(f"Map: {result.map_name}")
    print(f"Game Type: {result.game_type}")
    print(f"Players: {result.num_players}/{result.max_players}")

    print("\nPlayers:")
    for player in result.players:
        print(f"  {player.name} (Ping: {player.ping}ms)")

    # Example raw data that might be useful for debugging
    print("\nRaw Data:")
    if hasattr(result, 'raw'):
        for key, value in result.raw.items():
            print(f"{key}: {value}")

    await handler.save_result("test_warcraft3_status", result) 