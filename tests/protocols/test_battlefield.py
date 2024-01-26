import pytest
from opengsq.protocols.battlefield import Battlefield

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# bf4
test = Battlefield(host="74.91.124.140", port=47200)


@pytest.mark.asyncio
async def test_get_info():
    result = await test.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_version():
    result = await test.get_version()
    await handler.save_result("test_get_version", result)


@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result("test_get_players", result)
