import pytest
from opengsq import Mordhau

from tests.test_helper import get_master_servers_from_steam

tests = []

# Get some servers from steam for testing
server_list = get_master_servers_from_steam(appid=629760)

# We use 3 servers for testing
server_list = server_list[:3]

for server in server_list:
    subs = server['addr'].split(':')
    tests.append(Mordhau(address=subs[0], query_port=int(subs[1]), timeout=5.0))

@pytest.mark.asyncio
async def test_query():
    for test in tests:
        server = await test.query()
        print(server.to_json(indent=4))
