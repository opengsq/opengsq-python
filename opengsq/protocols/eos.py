import aiohttp
import base64
import json

from opengsq.exceptions import ServerNotFoundException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import Socket


class EOS(ProtocolBase):
    """Epic Online Services (EOS) Protocol"""
    full_name = 'Epic Online Services (EOS) Protocol'

    _api_url = 'https://api.epicgames.dev'

    def __init__(self, host: str, port: int, timeout: float = 5, client_id: str = None, client_secret: str = None, deployment_id: str = None):
        super().__init__(host, port, timeout)

        if client_id is None or client_secret is None or deployment_id is None:
            raise ValueError(
                "client_id, client_secret, and deployment_id must not be None")

        self.client_id = client_id
        self.client_secret = client_secret
        self.deployment_id = deployment_id
        self.access_token = None

    async def _get_access_token(self) -> str:
        url = f'{self._api_url}/auth/v1/oauth/token'
        body = f"grant_type=client_credentials&deployment_id={self.deployment_id}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode('utf-8')).decode('utf-8')}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=body, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        return data["access_token"]

    async def _get_matchmaking(self, data: dict):
        if self.access_token is None:
            self.access_token = await self._get_access_token()
            assert self.access_token is not None, "Failed to get access token"

        url = f"{self._api_url}/matchmaking/v1/{self.deployment_id}/filter"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(data), headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        return data

    async def get_info(self) -> dict:
        address = await Socket.gethostbyname(self._host)
        address_bound_port = f':{self._port}'

        data = await self._get_matchmaking({
            "criteria": [
                {
                    "key": "attributes.ADDRESS_s",
                    "op": "EQUAL",
                    "value": address
                },
                {
                    "key": "attributes.ADDRESSBOUND_s",
                    "op": "CONTAINS",
                    "value": address_bound_port
                },
            ]
        })

        if data["count"] <= 0:
            raise ServerNotFoundException()

        return data['sessions'][0]


if __name__ == '__main__':
    import asyncio

    async def main_async():
        client_id = 'xyza7891muomRmynIIHaJB9COBKkwj6n'
        client_secret = 'PP5UGxysEieNfSrEicaD1N2Bb3TdXuD7xHYcsdUHZ7s'
        deployment_id = 'ad9a8feffb3b4b2ca315546f038c3ae2'

        eos = EOS(host='5.62.115.46', port=7783, timeout=5.0, client_id=client_id,
                  client_secret=client_secret, deployment_id=deployment_id)
        data = await eos.get_info()
        print(json.dumps(data, indent=None) + '\n')

    asyncio.run(main_async())
