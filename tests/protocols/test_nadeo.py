import pytest
from opengsq.protocols.nadeo import Nadeo

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# Test server configuration
SERVER_IP = "192.168.100.2"
SERVER_PORT = 5000
SERVER_USER = "SuperAdmin"
SERVER_PASSWORD = "SuperAdmin"

nadeo = Nadeo(host=SERVER_IP, port=SERVER_PORT)


@pytest.mark.asyncio
async def test_authenticate():
    result = await nadeo.authenticate(SERVER_USER, SERVER_PASSWORD)
    assert result is True


@pytest.mark.asyncio
async def test_get_status():
    await nadeo.authenticate(SERVER_USER, SERVER_PASSWORD)
    result = await nadeo.get_status()
    await handler.save_result("test_get_status", result)


@pytest.mark.asyncio
async def test_get_map_info():
    await nadeo.authenticate(SERVER_USER, SERVER_PASSWORD)
    result = await nadeo.get_status()
    print(f"Server: {result.server_options.name}")
    print(f"Map: {result.map_info.name}")
    print(f"Author: {result.map_info.author}")
    print(f"Players: {len(result.players)}/{result.server_options.max_players}")
    assert result.map_info.name != ""
    assert result.server_options.name != ""
