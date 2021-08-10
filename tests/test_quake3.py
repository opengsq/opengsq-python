import opengsq
import pytest


test = opengsq.Quake3(address='85.10.197.106', query_port=27960)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)