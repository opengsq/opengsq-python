import os

import pytest
from opengsq.protocols.minecraft import Minecraft

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# Minecraft
test = Minecraft(host='valistar.site', port=25565)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)

@pytest.mark.asyncio
async def test_get_status_pre17():
    result = await test.get_status_pre17()
    await handler.save_result('test_get_status_pre17', result)
