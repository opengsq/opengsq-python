import pytest
from opengsq.protocols.gamespy4 import GameSpy4

from .result_handler import ResultHandler

handler = ResultHandler('test_gamespy4')
# handler.enable_save = True

test = GameSpy4(address='104.238.152.181', query_port=19132)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
