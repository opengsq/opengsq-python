import pytest
from opengsq.rcon_protocols.source_rcon import SourceRcon

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True


@pytest.mark.asyncio
async def test_authenticate():
    return

    with SourceRcon("", 27015) as rcon:
        await rcon.authenticate("")
        response = await rcon.send_command("cvarlist")
        await handler.save_result("test_authenticate", response, is_json=False)
