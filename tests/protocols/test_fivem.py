import os

import pytest
from opengsq.protocols.fivem import FiveM

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# FiveM
fivem = FiveM(host='185.254.99.12', port=30120)


@pytest.mark.asyncio
async def test_get_info():
    result = await fivem.get_info()
    await handler.save_result('test_get_info', result)


@pytest.mark.asyncio
async def test_get_players():
    result = await fivem.get_players()
    await handler.save_result('test_get_players', result)


@pytest.mark.asyncio
async def test_get_dynamic():
    result = await fivem.get_dynamic()
    await handler.save_result('test_get_dynamic', result)
