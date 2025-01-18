import pytest
from opengsq.protocols.palworld import Palworld

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# Palworld
test = Palworld(
    host="79.136.0.124",
    port=8212,
    api_username="admin",
    api_password="",
)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
