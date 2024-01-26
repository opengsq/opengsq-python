import pytest
from opengsq.protocols.raknet import RakNet

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# Raknet
test = RakNet(host="mc.advancius.net", port=19132)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
