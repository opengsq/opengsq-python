import os

import pytest
from opengsq.protocols.raknet import Raknet

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
handler.enable_save = True

# Raknet
test = Raknet(address='193.70.94.83', query_port=19132)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
