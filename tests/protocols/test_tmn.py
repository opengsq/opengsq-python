import pytest
from opengsq.protocols.tmn import TMN

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True
handler.delay_per_test = 1

# tmn
tmn = TMN(host="172.29.100.25")


@pytest.mark.asyncio
async def test_get_info():
    result = await tmn.get_status()
    await handler.save_result("test_get_status", result) 