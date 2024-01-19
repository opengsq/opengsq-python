import os

import pytest
from opengsq.protocols.eos import EOS

from .result_handler import ResultHandler

handler = ResultHandler(os.path.basename(__file__)[:-3])
# handler.enable_save = True

# ARK: Survival Ascended
client_id = 'xyza7891muomRmynIIHaJB9COBKkwj6n'
client_secret = 'PP5UGxysEieNfSrEicaD1N2Bb3TdXuD7xHYcsdUHZ7s'
deployment_id = 'ad9a8feffb3b4b2ca315546f038c3ae2'

eos = EOS(host='5.62.115.46', port=7783, client_id=client_id,
            client_secret=client_secret, deployment_id=deployment_id)


@pytest.mark.asyncio
async def test_get_info():
    result = await eos.get_info()
    await handler.save_result('test_get_info', result)
