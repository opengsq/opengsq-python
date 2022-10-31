import pytest
from opengsq.protocols.gamespy2 import GameSpy2

from .result_handler import ResultHandler

handler = ResultHandler('test_gamespy2')
# handler.enable_save = True

test = GameSpy2(address='158.69.118.94', query_port=23000)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
