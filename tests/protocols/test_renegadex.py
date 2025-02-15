import pytest
from opengsq.protocols.renegadex import RenegadeX
from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

@pytest.mark.asyncio
async def test_renegadex_status():
    rx = RenegadeX(host="10.13.37.149")
    result = await rx.get_status()

    print("\nRenegade X Server Details:")
    print(f"Server Name: {result.name}")
    print(f"Current Map: {result.current_map}")
    print(f"Game Version: {result.game_version}")
    print(f"Players: {result.players}/{result.variables.player_limit}")
    print(f"Port: {result.port}")

    print("\nServer Settings:")
    print(f"Vehicle Limit: {result.variables.vehicle_limit}")
    print(f"Mine Limit: {result.variables.mine_limit}")
    print(f"Time Limit: {result.variables.time_limit}")
    print(f"Team Mode: {result.variables.team_mode}")
    print(f"Game Type: {result.variables.game_type}")

    print("\nServer Flags:")
    print(f"Password Protected: {'Yes' if result.variables.passworded else 'No'}")
    print(f"Steam Required: {'Yes' if result.variables.steam_required else 'No'}")
    print(f"Spawn Crates: {'Yes' if result.variables.spawn_crates else 'No'}")
    print(f"Ranked: {'Yes' if result.variables.ranked else 'No'}")

    await handler.save_result("test_renegadex_status", result)