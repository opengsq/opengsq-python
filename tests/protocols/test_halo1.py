import pytest
from opengsq.protocols.halo1 import Halo1

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

# bfv
test = Halo1(host="172.29.100.29", port=2302)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
