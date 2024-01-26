import pytest
from opengsq.protocols.vcmp import Vcmp

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# Vice City Multiplayer
test = Vcmp(host="51.178.65.136", port=8114)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)


@pytest.mark.asyncio
async def test_get_players():
    result = await test.get_players()
    await handler.save_result("test_get_players", result)
