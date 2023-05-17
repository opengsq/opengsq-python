import os

import pytest
from opengsq.protocols.gamespy2 import GameSpy2

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

test = GameSpy2(host='89.58.8.211', port=23000)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
