import aiohttp
import time

from opengsq.protocol_base import ProtocolBase


class FiveM(ProtocolBase):
    """FiveM Protocol (https://docs.fivem.net/docs/server-manual/proxy-setup/)"""
    full_name = 'FiveM Protocol'

    async def _get(self, filename: str) -> dict:
        url = f'http://{self._host}:{self._port}/{filename}.json?v={int(time.time())}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json(content_type=None)

    async def get_info(self) -> dict:
        return await self._get('info')

    async def get_players(self) -> list:
        return await self._get('players')

    async def get_dynamic(self) -> dict:
        return await self._get('dynamic')


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        fivem = FiveM(host='144.217.10.12', port=30120, timeout=5.0)
        info = await fivem.get_info()
        print(json.dumps(info, indent=None) + '\n')
        players = await fivem.get_players()
        print(json.dumps(players, indent=None) + '\n')
        dynamic = await fivem.get_dynamic()
        print(json.dumps(dynamic, indent=None) + '\n')

    asyncio.run(main_async())
