import pytest
from opengsq.protocols.cod4 import CoD4


from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

class TestCoD4:
    @pytest.mark.asyncio
    async def test_get_info(self):
        cod4 = CoD4(host="172.29.101.68", port=28960, timeout=5.0)
        info = await cod4.get_info()
        assert info is not None
        # Check that we got some basic info
        assert hasattr(info, 'hostname')
        assert hasattr(info, 'mapname')
        assert hasattr(info, 'gametype')
        await handler.save_result("test_get_info", info)

    @pytest.mark.asyncio
    async def test_get_status(self):
        cod4 = CoD4(host="172.29.101.68", port=28960, timeout=5.0)
        status = await cod4.get_status()
        assert status is not None
        # Check that we got some basic status info
        assert hasattr(status, 'sv_hostname')
        assert hasattr(status, 'mapname')
        assert hasattr(status, 'gamename')
        await handler.save_result("test_get_status", status)
    @pytest.mark.asyncio
    async def test_get_full_status(self):
        cod4 = CoD4(host="172.29.101.68", port=28960, timeout=5.0)
        full_status = await cod4.get_full_status()
        assert full_status is not None
        assert full_status.info is not None
        assert full_status.status is not None
        await handler.save_result("test_get_full_status", full_status)
    @pytest.mark.asyncio
    async def test_protocol_properties(self):
        cod4 = CoD4(host="172.29.101.68", port=28960)
        assert cod4.full_name == "Call of Duty 4 Protocol"
        assert cod4._source_port == 28960
        await handler.save_result("test_protocol_properties", cod4)







