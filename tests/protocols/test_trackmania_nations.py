import pytest
from opengsq.protocols.trackmania_nations import TrackmaniaNations

from ..result_handler import ResultHandler


handler = ResultHandler(__file__)
handler.enable_save = True

# Test server configuration
SERVER_IP = "172.29.100.29"
SERVER_PORT = 2350

tmn = TrackmaniaNations(host=SERVER_IP, port=SERVER_PORT)


@pytest.mark.asyncio
async def test_get_info():
    result = await tmn.get_info()
    await handler.save_result("test_get_info", result)




