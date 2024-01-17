import os

import pytest
from opengsq.protocols.satisfactory import Satisfactory

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# Satisfactory
test = Satisfactory(host='79.136.0.124', port=15777)

@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result('test_get_status', result)
