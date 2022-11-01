import os

import pytest
from opengsq.protocols.samp import Samp

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# San Andreas Multiplayer
test = Samp(address='51.254.178.238', query_port=7777)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)

@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result('test_get_players', result)

@pytest.mark.asyncio
async def test_get_rules():
    result = await test.get_rules()
    await handler.save_result('test_get_rules', result)
