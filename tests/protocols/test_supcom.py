import pytest
from opengsq.protocols.supcom import SupCom

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

# Supreme Commander
test = SupCom(
    host="172.29.100.29"
)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)

