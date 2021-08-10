import opengsq
import pytest


test = opengsq.Quake2(address='46.165.236.118', query_port=27910)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)
