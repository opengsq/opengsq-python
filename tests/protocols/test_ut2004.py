import pytest
from opengsq.protocols.ut2004 import UT2004

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

test = UT2004(host="37.187.146.47", port=7787, timeout=5.0)


@pytest.mark.asyncio
async def test_get_info():
    result = await test.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result("test_get_players", result)


@pytest.mark.asyncio
async def test_get_rules():
    result = await test.get_rules()
    await handler.save_result("test_get_rules", result)


@pytest.mark.asyncio
async def test_get_full_status():
    result = await test.get_full_status()
    await handler.save_result("test_get_full_status", result)
