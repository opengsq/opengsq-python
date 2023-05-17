import os

import pytest
from opengsq.protocols.quake3 import Quake3

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

test = Quake3(host='108.61.18.110', port=27960)

@pytest.mark.asyncio
async def test_get_info():
    result = await test.get_info()
    await handler.save_result('test_get_info', result)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
