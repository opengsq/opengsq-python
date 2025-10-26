import pytest
from opengsq.protocols.stronghold_ce import StrongholdCE

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

# StrongHold: Crusader Europe
stronghold_ce = StrongholdCE(host="172.29.100.29")


@pytest.mark.asyncio
async def test_get_status():
    result = await stronghold_ce.get_status()
    await handler.save_result("test_get_status", result)
