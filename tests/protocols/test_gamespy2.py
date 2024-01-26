import pytest
from opengsq.protocols.gamespy2 import GameSpy2

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# bfv
test = GameSpy2(host="108.61.236.22", port=23000)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
