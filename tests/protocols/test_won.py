import pytest
from opengsq.protocols.won import WON

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# Counter-Strike 1.5
won = WON(host="212.227.190.150", port=27020)


@pytest.mark.asyncio
async def test_get_info():
    result = await won.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_players():
    result = await won.get_players()
    await handler.save_result("test_get_players", result)


@pytest.mark.asyncio
async def test_get_rules():
    result = await won.get_rules()
    await handler.save_result("test_get_rules", result)
