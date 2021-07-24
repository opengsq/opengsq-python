from typing import List

import pytest
from opengsq.protocols import Source

from .test_helper import get_master_servers_from_steam


tests: List[Source] = []

# Get some servers from steam for testing
server_list = get_master_servers_from_steam(appid=440, limit=1000)

# We use 1 server for testing
server_list = server_list[:0]

for server in server_list:
    subs = server['addr'].split(':')
    tests.append(Source(address=subs[0], query_port=int(subs[1])))


@pytest.mark.asyncio
async def test_get_info():
    for test in tests:
        response = await test.get_info()
        print(response)


@pytest.mark.asyncio
async def test_get_players():
    for test in tests:
        response = await test.get_players()
        print(response)


@pytest.mark.asyncio
async def test_get_rules():
    for test in tests:
        response = await test.get_rules()
        print(response)
