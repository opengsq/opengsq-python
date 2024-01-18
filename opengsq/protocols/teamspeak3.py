from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import TcpClient


class TeamSpeak3(ProtocolBase):
    """TeamSpeak 3 Protocol"""
    full_name = 'TeamSpeak 3 Protocol'

    def __init__(self, host: str, port: int, voice_port: int, timeout: float = 5):
        super().__init__(host, port, timeout)
        self._voice_port = voice_port

    async def get_info(self):
        response = await self.__send_and_receive(b'serverinfo')
        return self.__parse_kvs(response)

    async def get_clients(self):
        response = await self.__send_and_receive(b'clientlist')
        return self.__parse_rows(response)

    async def get_channels(self):
        response = await self.__send_and_receive(b'channellist -topic')
        return self.__parse_rows(response)

    async def __send_and_receive(self, data: bytes):
        with TcpClient() as tcpClient:
            tcpClient.settimeout(self._timeout)
            await tcpClient.connect((self._host, self._port))

            # b'TS3\n\rWelcome to the TeamSpeak 3 ServerQuery interface,
            # type "help" for a list of commands and "help <command>" for information on a specific command.\n\r'
            await tcpClient.recv()

            # b'error id=0 msg=ok\n\r'
            tcpClient.send(f'use port={self._voice_port}\n'.encode())
            await tcpClient.recv()

            tcpClient.send(data + b'\x0A')
            response = b''

            while not response.endswith(b'error id=0 msg=ok\n\r'):
                response += await tcpClient.recv()

        # Remove last bytes b'\n\rerror id=0 msg=ok\n\r'
        return response[:-21]

    def __parse_rows(self, response: bytes):
        return [self.__parse_kvs(row) for row in response.split(b'|')]

    def __parse_kvs(self, response: bytes):
        kvs = {}

        for kv in response.split(b' '):
            items = kv.split(b'=', 1)
            key = str(items[0], encoding='utf-8', errors='ignore')
            val = str(items[1], encoding='utf-8', errors='ignore') if len(items) == 2 else ""
            kvs[key] = val.replace('\\p', '|').replace('\\s', ' ').replace('\\/', '/')

        return kvs


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        teamspeak3 = TeamSpeak3(host='145.239.200.2', port=10011, voice_port=9987, timeout=5.0)
        info = await teamspeak3.get_info()
        print(json.dumps(info, indent=None) + '\n')
        clients = await teamspeak3.get_clients()
        print(json.dumps(clients, indent=None) + '\n')
        channels = await teamspeak3.get_channels()
        print(json.dumps(channels, indent=None) + '\n')

    asyncio.run(main_async())
