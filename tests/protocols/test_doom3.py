import os

import pytest
from opengsq.protocols.doom3 import Doom3

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# Quake 4
doom3 = Doom3(host='178.162.135.83', port=27735)

@pytest.mark.asyncio
async def test_get_info():
    result = await doom3.get_info()
    await handler.save_result('test_get_info', result)
