import os

import pytest
from opengsq.protocols.scum import Scum

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# Scum
test = Scum(host='15.235.181.19', port=7042)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)

@pytest.mark.asyncio
async def test_query_master_servers():
    result = await test.query_master_servers()
    await handler.save_result('test_query_master_servers', result)
