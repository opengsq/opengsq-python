import pytest
from opengsq.protocols.eldewrito import ElDewrito

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True
handler.delay_per_test = 1

# tf2
eldewrito = ElDewrito(host="172.29.100.29", port=11774)


@pytest.mark.asyncio
async def test_get_info():
    result = await eldewrito.get_status()
    await handler.save_result("test_get_status", result)
