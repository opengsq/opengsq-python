import os

import pytest
from opengsq.protocols.killingfloor import KillingFloor

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# Killing Floor
test = KillingFloor(host='185.80.128.168', port=7708)

@pytest.mark.asyncio
async def test_get_details():
    result = await test.get_details()
    await handler.save_result('test_get_details', result)

@pytest.mark.asyncio
async def test_get_rules():
    result = await test.get_rules()
    await handler.save_result('test_get_rules', result)

@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result('test_get_players', result)
