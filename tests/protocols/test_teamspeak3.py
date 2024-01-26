import pytest
from opengsq.protocols.teamspeak3 import TeamSpeak3

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# TeamSpeak 3
test = TeamSpeak3(host="145.239.200.2", port=10011, voice_port=9987)


@pytest.mark.asyncio
async def test_get_info():
    result = await test.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_clients():
    result = await test.get_clients()
    await handler.save_result("test_get_clients", result)


@pytest.mark.asyncio
async def test_get_channels():
    result = await test.get_channels()
    await handler.save_result("test_get_channels", result)
