import pytest
from opengsq.protocols.ase import ASE
from .result_handler import ResultHandler


handler = ResultHandler('test_ase')
# handler.enable_save = True

# Grand Theft Auto: San Andreas - Multi Theft Auto
ase = ASE('79.137.97.3', 22126)

@pytest.mark.asyncio
async def test_get_status():
    result = await ase.get_status()
    await handler.save_result('test_get_status', result)
