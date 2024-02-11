import pytest
from opengsq.protocols.kaillera import Kaillera

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

test = Kaillera(host="112.161.44.113", port=27888)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)


@pytest.mark.asyncio
async def test_query_master_servers():
    result = await test.query_master_servers()
    await handler.save_result("test_query_master_servers", result)
