import os

import pytest
from opengsq.protocols.gamespy3 import GameSpy3

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

test = GameSpy3(host='95.172.92.116', port=29900)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
