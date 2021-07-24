import asyncio

import pytest
from opengsq.protocols import GameSpy3


test = GameSpy3(address='185.107.96.59', query_port=29900)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)
