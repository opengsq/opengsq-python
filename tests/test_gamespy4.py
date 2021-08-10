import opengsq
import pytest


test = opengsq.GameSpy4(address='104.238.152.181', query_port=19132)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)
