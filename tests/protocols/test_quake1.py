import pytest
from opengsq.protocols.quake1 import Quake1
from .result_handler import ResultHandler


handler = ResultHandler('test_quake1')
# handler.enable_save = True

# https://www.quakeservers.net/quakeworld/servers/so=8/
test = Quake1(address='qw.servegame.org', query_port=27500)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
