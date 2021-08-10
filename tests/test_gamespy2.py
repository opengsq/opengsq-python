import asyncio

import opengsq
import pytest


test = opengsq.GameSpy2(address='158.69.118.94', query_port=23000)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)
    await asyncio.sleep(1)
