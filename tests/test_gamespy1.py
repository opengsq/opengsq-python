import asyncio

import pytest
from opengsq.protocols import GameSpy1


test = GameSpy1(address='139.162.235.20', query_port=7778)

@pytest.mark.asyncio
async def test_get_basic():
    response = await test.get_basic()
    print(response)
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_get_info():
    response = await test.get_info()
    print(response)
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_get_rules():
    response = await test.get_rules()
    print(response)
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_get_players():
    response = await test.get_players()
    print(response)
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_get_teams():
    response = await test.get_teams()
    print(response)
    await asyncio.sleep(1)
