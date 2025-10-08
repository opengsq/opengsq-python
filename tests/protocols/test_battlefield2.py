import pytest
from opengsq.protocols.battlefield2 import Battlefield2

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

# Example Battlefield 2 server - you may need to update with a real server
test = Battlefield2(host="172.29.100.29", port=29900)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
