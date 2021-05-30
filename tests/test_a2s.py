import pytest
from opengsq.protocols import A2S

from .test_helper import get_master_servers_from_steam

tests = []

# Get some servers from steam for testing
server_list = get_master_servers_from_steam(appid=440)

# We use 3 servers for testing
server_list = server_list[:3]

for server in server_list:
    subs = server['addr'].split(':')
    tests.append(A2S(address=subs[0], query_port=int(subs[1]), timeout=5.0, engine=A2S.SOURCE))


@pytest.mark.asyncio
async def test_query():
    for test in tests:
        server = await test.query()
        print(server.to_json(indent=4))


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
