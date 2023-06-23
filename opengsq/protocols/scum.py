from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import ServerNotFoundException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync, SocketKind


class Scum(ProtocolBase):
    """Scum Protocol"""
    full_name = 'Scum Protocol'

    async def get_status(self, master_servers: list = None) -> dict:
        """
        Retrieves information about the server
        Notice: this method calls Scum.query_master_servers()
        function everytime if master_servers is not passed,
        you may need to cache the master servers if you had
        lots of servers to query.
        """
        ip = SocketAsync.gethostbyname(self._host)

        if master_servers is None:
            master_servers = await Scum.query_master_servers()

        for server in master_servers:
            if server['ip'] == ip:
                return server

        raise ServerNotFoundException()

    @staticmethod
    async def query_master_servers(host='172.107.16.215', port=1040) -> list:
        """
        Query SCUM Master-Server list
        """
        with SocketAsync(SocketKind.SOCK_STREAM) as sock:
            sock.settimeout(5)
            await sock.connect((host, port))
            sock.send(b'\x04\x03\x00\x00')

            total = -1
            response = b''
            servers = []

            while total == -1 or len(servers) < total:
                response += await sock.recv()
                br = BinaryReader(response)

                # first packet return the total number of servers
                if total == -1:
                    total = br.read_short()

                # server bytes length always 127
                while br.length() >= 127:
                    server = {}
                    server['ip'] = '.'.join(map(str, reversed([br.read_byte(), br.read_byte(), br.read_byte(), br.read_byte()])))
                    server['port'] = br.read_short()
                    server['name'] = str(br.read_bytes(100).rstrip(b'\x00'), encoding='utf-8', errors='ignore')
                    br.read_byte()  # skip
                    server['numplayers'] = br.read_byte()
                    server['maxplayers'] = br.read_byte()
                    server['time'] = br.read_byte()
                    br.read_byte()  # skip
                    server['password'] = ((br.read_byte() >> 1) & 1) == 1
                    br.read_bytes(7)  # skip
                    v = list(reversed([hex(br.read_byte())[2:].rjust(2, '0') for _ in range(8)]))
                    server['version'] = f'{int(v[0], 16)}.{int(v[1], 16)}.{int(v[2] + v[3], 16)}.{int(v[4] + v[5] + v[6] + v[7], 16)}'
                    servers.append(server)

                # if the length is less than 127, save the unused bytes for next loop
                response = br.read()

        return servers


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        scum = Scum(host='15.235.181.19', port=7042, timeout=5.0)
        master_servers = await scum.query_master_servers()
        server = await scum.get_status(master_servers)
        print(json.dumps(server, indent=None) + '\n')

    asyncio.run(main_async())
