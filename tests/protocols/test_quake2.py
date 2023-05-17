import os

import pytest
from opengsq.protocols.quake2 import Quake2

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

test = Quake2(host='46.165.236.118', port=27910)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
