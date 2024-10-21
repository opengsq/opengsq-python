import pytest
from opengsq.protocols.satisfactory import Satisfactory

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True

# Satisfactory
test = Satisfactory(
    host="79.136.0.124",
    port=7777,
    app_token="ewoJInBsIjogIkFQSVRva2VuIgp9.EE80F05DAFE991AE8850CD4CFA55840D9F41705952A96AF054561ABA3676BE4D4893B162271D3BC0A0CC50797219D2C8E627F0737FC8776F3468EA44B3700EF7",
)


@pytest.mark.asyncio
async def test_get_status():
    result = await test.get_status()
    await handler.save_result("test_get_status", result)
