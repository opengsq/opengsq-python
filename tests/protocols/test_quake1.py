import pytest
from opengsq.protocols.quake1 import Quake1

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# https://www.quakeservers.net/quakeworld/servers/so=8/
test = Quake1(host="35.185.44.174", port=27500)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
