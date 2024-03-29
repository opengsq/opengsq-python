import pytest
from opengsq.protocols.quake3 import Quake3

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

test = Quake3(host="135.148.137.185", port=27960)


@pytest.mark.asyncio
async def test_get_info():
    result = await test.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
