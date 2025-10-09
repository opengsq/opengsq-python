import pytest
from opengsq.protocols.cod1 import CoD1


from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

class TestCoD1:
    @pytest.mark.asyncio
    async def test_get_info(self):
        cod1 = CoD1(host="172.29.100.29", port=28960, timeout=5.0)
        info = await cod1.get_info()
        assert info is not None
        # Check that we got some basic info
        assert hasattr(info, 'hostname')
        assert hasattr(info, 'mapname')
        assert hasattr(info, 'gametype')
        await handler.save_result("test_get_info", info)

    @pytest.mark.asyncio
    async def test_get_status(self):
        cod1 = CoD1(host="172.29.100.29", port=28960, timeout=5.0)
        status = await cod1.get_status()
        assert status is not None
        # Check that we got some basic status info
        assert hasattr(status, 'sv_hostname')
        assert hasattr(status, 'mapname')
        assert hasattr(status, 'gamename')
        await handler.save_result("test_get_status", status)
    @pytest.mark.asyncio
    async def test_get_full_status(self):
        cod1 = CoD1(host="172.29.100.29", port=28960, timeout=5.0)
        full_status = await cod1.get_full_status()
        assert full_status is not None
        assert full_status.info is not None
        assert full_status.status is not None
        await handler.save_result("test_get_full_status", full_status)
    @pytest.mark.asyncio
    async def test_protocol_properties(self):
        cod1 = CoD1(host="172.29.100.29", port=28960)
        assert cod1.full_name == "Call of Duty 1 Protocol"
        assert cod1._source_port == 28960
        await handler.save_result("test_protocol_properties", cod1)







