import pytest
from opengsq.protocols.cod4 import CoD4


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

    @pytest.mark.asyncio
    async def test_get_status(self):
        cod4 = CoD4(host="172.29.101.68", port=28960, timeout=5.0)
        status = await cod4.get_status()
        assert status is not None
        # Check that we got some basic status info
        assert hasattr(status, 'sv_hostname')
        assert hasattr(status, 'mapname')
        assert hasattr(status, 'gamename')

    @pytest.mark.asyncio
    async def test_get_full_status(self):
        cod4 = CoD4(host="172.29.101.68", port=28960, timeout=5.0)
        full_status = await cod4.get_full_status()
        assert full_status is not None
        assert full_status.info is not None
        assert full_status.status is not None

    def test_protocol_properties(self):
        cod4 = CoD4(host="172.29.101.68", port=28960)
        assert cod4.full_name == "Call of Duty 4 Protocol"
        assert cod4._source_port == 28960







