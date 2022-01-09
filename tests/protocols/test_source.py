import pytest
from opengsq.protocols.source import Source
from ..result_handler import ResultHandler


handler = ResultHandler('test_source')
# handler.enable_save = True

# tf2
source = Source('91.216.250.14', 27015)

@pytest.mark.asyncio
async def test_get_info():
    result = await source.get_info()
    await handler.save_result('test_get_info', result)

@pytest.mark.asyncio
async def test_get_players():
    result = await source.get_players()
    await handler.save_result('test_get_players', result)

@pytest.mark.asyncio
async def test_get_rules():
    result = await source.get_rules()
    await handler.save_result('test_get_rules', result)
