import pytest
from opengsq.protocols.ssc import SSC

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True
handler.delay_per_test = 1

test = SSC(host="172.29.100.29", port=25601)


@pytest.mark.asyncio
async def test_get_basic():
    result = await test.get_basic()
    await handler.save_result("test_get_basic", result)


@pytest.mark.asyncio
async def test_get_info():
    result = await test.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_rules():
    result = await test.get_rules()
    await handler.save_result("test_get_rules", result)


@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result("test_get_players", result)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)


@pytest.mark.asyncio
async def test_get_teams():
    result = await test.get_teams()
    await handler.save_result("test_get_teams", result)
