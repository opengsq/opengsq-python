import pytest
from opengsq.protocols.jediknight import JediKnight


from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

class TestJediKnight:
    @pytest.mark.asyncio
    async def test_get_info(self):
        jk = JediKnight(host="172.29.100.29", port=29070, timeout=5.0)
        info = await jk.get_info()
        assert info is not None
        # Check that we got some basic info
        assert hasattr(info, 'hostname')
        assert hasattr(info, 'mapname')
        assert hasattr(info, 'gametype')
        await handler.save_result("test_get_info", info)

    @pytest.mark.asyncio
    async def test_get_status(self):
        jk = JediKnight(host="172.29.100.29", port=29070, timeout=5.0)
        status = await jk.get_status()
        assert status is not None
        # Check that we got some basic status info
        assert hasattr(status, 'sv_hostname')
        assert hasattr(status, 'mapname')
        assert hasattr(status, 'gamename')
        assert hasattr(status, 'players')
        await handler.save_result("test_get_status", status)

    @pytest.mark.asyncio
    async def test_get_full_status(self):
        jk = JediKnight(host="172.29.100.29", port=29070, timeout=5.0)
        full_status = await jk.get_full_status()
        assert full_status is not None
        assert full_status.info is not None
        assert full_status.status is not None
        await handler.save_result("test_get_full_status", full_status)

    @pytest.mark.asyncio
    async def test_protocol_properties(self):
        jk = JediKnight(host="172.29.100.29", port=29070)
        assert jk.full_name == "Star Wars Jedi Knight - Jedi Academy Protocol"
        assert jk._source_port == 29070
        await handler.save_result("test_protocol_properties", jk)

