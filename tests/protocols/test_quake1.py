import os

import pytest
from opengsq.protocols.quake1 import Quake1

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# https://www.quakeservers.net/quakeworld/servers/so=8/
test = Quake1(host='qw.servegame.org', port=27500)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
