import pytest
from opengsq.protocols.eos import EOS

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
# handler.enable_save = True


@pytest.mark.asyncio
async def test_get_matchmaking():
    # The Isle - EVRIMA
    client_id = "xyza7891gk5PRo3J7G9puCJGFJjmEguW"
    client_secret = "pKWl6t5i9NJK8gTpVlAxzENZ65P8hYzodV8Dqe5Rlc8"
    deployment_id = "6db6bea492f94b1bbdfcdfe3e4f898dc"
    grant_type = "client_credentials"
    external_auth_type = ""
    external_auth_token = ""

    access_token = await EOS.get_access_token(
        client_id=client_id,
        client_secret=client_secret,
        deployment_id=deployment_id,
        grant_type=grant_type,
        external_auth_type=external_auth_type,
        external_auth_token=external_auth_token,
    )

    matchmaking = await EOS.get_matchmaking(deployment_id, access_token)
    await handler.save_result("test_get_matchmaking", matchmaking)


@pytest.mark.asyncio
async def test_get_info():
    # Ark: Survival Ascended
    client_id = "xyza7891muomRmynIIHaJB9COBKkwj6n"
    client_secret = "PP5UGxysEieNfSrEicaD1N2Bb3TdXuD7xHYcsdUHZ7s"
    deployment_id = "ad9a8feffb3b4b2ca315546f038c3ae2"
    grant_type = "client_credentials"
    external_auth_type = ""
    external_auth_token = ""

    access_token = await EOS.get_access_token(
        client_id=client_id,
        client_secret=client_secret,
        deployment_id=deployment_id,
        grant_type=grant_type,
        external_auth_type=external_auth_type,
        external_auth_token=external_auth_token,
    )

    eos = EOS(
        host="5.62.115.46",
        port=7783,
        deployment_id=deployment_id,
        access_token=access_token,
        timeout=5.0,
    )

    result = await eos.get_info()
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_info_palworld():
    # Palworld
    client_id = "xyza78916PZ5DF0fAahu4tnrKKyFpqRE"
    client_secret = "j0NapLEPm3R3EOrlQiM8cRLKq3Rt02ZVVwT0SkZstSg"
    deployment_id = "0a18471f93d448e2a1f60e47e03d3413"
    grant_type = "external_auth"
    external_auth_type = "deviceid_access_token"  # https://dev.epicgames.com/docs/web-api-ref/connect-web-api
    external_auth_token = await EOS.get_external_auth_token(
        client_id=client_id,
        client_secret=client_secret,
        external_auth_type=external_auth_type,
    )

    access_token = await EOS.get_access_token(
        client_id=client_id,
        client_secret=client_secret,
        deployment_id=deployment_id,
        grant_type=grant_type,
        external_auth_type=external_auth_type,
        external_auth_token=external_auth_token,
    )

    eos = EOS(
        host="34.142.202.135",
        port=30112,
        deployment_id=deployment_id,
        access_token=access_token,
        timeout=5.0,
    )

    result = await eos.get_info()
    await handler.save_result("test_get_info_palworld", result)
