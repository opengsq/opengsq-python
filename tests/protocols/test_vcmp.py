import os

import pytest
from opengsq.protocols.vcmp import Vcmp

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# Vice City Multiplayer
test = Vcmp(address='91.121.134.5', query_port=8192)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)

@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result('test_get_players', result)
