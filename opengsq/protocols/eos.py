from __future__ import annotations

from typing import Any
import aiohttp
import base64
import json

from opengsq.exceptions import ServerNotFoundException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import Socket
from opengsq.responses.eos import Matchmaking


class EOS(ProtocolBase):
    """
    This class represents the Epic Online Services (EOS) Protocol. It provides methods to interact with the EOS API.
    """

    full_name = "Epic Online Services (EOS) Protocol"

    _api_url = "https://api.epicgames.dev"

    def __init__(
        self,
        host: str,
        port: int,
        deployment_id: str,
        access_token: str,
        timeout: float = 5,
    ):
        """
        Initializes the EOS object with the given parameters.

        :param host: The host of the server.
        :param port: The port of the server.
        :param timeout: The timeout for the server connection.
        :param deployment_id: The deployment ID for the EOS service.
        :param access_token: The access token for the EOS service.
        """
        super().__init__(host, port, timeout)

        if deployment_id is None or access_token is None:
            raise ValueError("deployment_id and access_token must not be None")

        self.deployment_id = deployment_id
        self.access_token = access_token

    @staticmethod
    async def get_access_token(
        *,
        client_id: str,
        client_secret: str,
        deployment_id: str,
        grant_type: str,
        external_auth_type: str,
        external_auth_token: str,
    ) -> str:
        """
        Retrieves the access token from the EOS service.

        :param client_id: The client ID for the EOS service.
        :param client_secret: The client secret for the EOS service.
        :param deployment_id: The deployment ID for the EOS service.
        :param grant_type: The grant type for the OAuth token.
        :param external_auth_type: The external authentication type.
        :param external_auth_token: The external authentication token.
        :return: The access token.
        """
        url = f"{EOS._api_url}/auth/v1/oauth/token"

        data = "&".join(
            [
                f"grant_type={grant_type}",
                f"external_auth_type={external_auth_type}",
                f"external_auth_token={external_auth_token}",
                "nonce=opengsq",
                f"deployment_id={deployment_id}",
                "display_name=User",
            ]
        )

        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        return data["access_token"]

    @staticmethod
    async def get_external_auth_token(
        *,
        client_id: str,
        client_secret: str,
        external_auth_type: str,
    ) -> str:
        """
        Retrieves the external authentication token from the EOS service.

        :param client_id: The client ID for the EOS service.
        :param client_secret: The client secret for the EOS service.
        :param external_auth_type: The external authentication type.
        :return: The external authentication token.
        """
        if external_auth_type == "deviceid_access_token":
            url = f"{EOS._api_url}/auth/v1/accounts/deviceid"

            data = "deviceModel=PC"

            headers = {
                "Authorization": f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()

            return data["access_token"]

        raise NotImplementedError(
            f"The external authentication type '{external_auth_type}' is not supported. Please provide a supported authentication type."
        )

    @staticmethod
    async def get_matchmaking(
        deployment_id: str, access_token: str, filter: dict = {}
    ) -> Matchmaking:
        """
        Retrieves the matchmaking data from the EOS service.

        :param deployment_id: The deployment ID for the EOS service.
        :param access_token: The access token for the EOS service.
        :param filter: The filter for the matchmaking data.
        :return: The matchmaking data.
        """
        url = f"{EOS._api_url}/matchmaking/v1/{deployment_id}/filter"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=json.dumps(filter), headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()

        return Matchmaking(sessions=data["sessions"], count=data["count"])

    async def get_info(self) -> dict[str, Any]:
        """
        Retrieves the matchmaking information for the current server.

        This method first resolves the host to an IP address, then queries the matchmaking service with the IP address and port.
        If no matching sessions are found, it raises a ServerNotFoundException.

        :return: The first matching session if any are found.
        """
        address = await Socket.gethostbyname(self._host)

        data = await self.get_matchmaking(
            self.deployment_id,
            self.access_token,
            {
                "criteria": [
                    {"key": "attributes.ADDRESS_s", "op": "EQUAL", "value": address},
                ]
            },
        )

        for session in data.sessions:
            attributes: dict = session.get("attributes", {})

            if (
                str(attributes.get("ADDRESSBOUND_s")).endswith(f":{self._port}")
                or attributes.get("GAMESERVER_PORT_l") == self._port
            ):
                return session

        raise ServerNotFoundException()


if __name__ == "__main__":
    import asyncio

    async def main_async():
        # The Isle - EVRIMA
        # client_id = "xyza7891gk5PRo3J7G9puCJGFJjmEguW"
        # client_secret = "pKWl6t5i9NJK8gTpVlAxzENZ65P8hYzodV8Dqe5Rlc8"
        # deployment_id = "6db6bea492f94b1bbdfcdfe3e4f898dc"
        # grant_type = "client_credentials"
        # external_auth_type = ""
        # external_auth_token = ""

        # Palworld
        # client_id = "xyza78916PZ5DF0fAahu4tnrKKyFpqRE"
        # client_secret = "j0NapLEPm3R3EOrlQiM8cRLKq3Rt02ZVVwT0SkZstSg"
        # deployment_id = "0a18471f93d448e2a1f60e47e03d3413"
        # grant_type = "external_auth"
        # external_auth_type = "deviceid_access_token"  # https://dev.epicgames.com/docs/web-api-ref/connect-web-api
        # external_auth_token = await EOS.get_external_auth_token(
        #     client_id=client_id,
        #     client_secret=client_secret,
        #     external_auth_type=external_auth_type,
        # )

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

        matchmaking = await EOS.get_matchmaking(deployment_id, access_token)
        print(
            json.dumps(matchmaking, indent=None, default=lambda dc: dc.__dict__) + "\n"
        )

        eos = EOS(
            host="5.62.115.46",
            port=7783,
            deployment_id=deployment_id,
            access_token=access_token,
            timeout=5.0,
        )

        info = await eos.get_info()
        print(json.dumps(info, indent=None, default=lambda dc: dc.__dict__) + "\n")

    asyncio.run(main_async())
