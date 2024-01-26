from __future__ import annotations

from opengsq.responses.scum import Status
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import ServerNotFoundException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import Socket, TcpClient


class Scum(ProtocolBase):
    """
    This class represents the Scum Protocol. It provides methods to interact with the Scum API.
    """

    full_name = "Scum Protocol"

    _master_servers = [
        ("176.57.138.2", 1040),
        ("172.107.16.215", 1040),
        ("206.189.248.133", 1040),
    ]

    async def get_status(self, master_servers: list[Status] = None) -> Status:
        """
        Asynchronously retrieves the status of the game server. If the master_servers parameter is not passed, this method calls the Scum.query_master_servers() function every time it is invoked. You may need to cache the master servers if you have a lot of servers to query.

        :param master_servers: A list of master servers. Defaults to None.
        :return: A Status object containing the status of the game server.
        """
        ip = await Socket.gethostbyname(self._host)

        if master_servers is None:
            master_servers = await Scum.query_master_servers()

        for server in master_servers:
            if server.ip == ip and server.port == self._port:
                return server

        raise ServerNotFoundException()

    @staticmethod
    async def query_master_servers() -> list[Status]:
        """
        Asynchronously queries the SCUM Master-Server list.

        :return: A list of Status objects containing the status of the master servers.
        """
        for host, port in Scum._master_servers:
            try:
                with TcpClient() as tcpClient:
                    tcpClient.settimeout(5)
                    await tcpClient.connect((host, port))
                    tcpClient.send(b"\x04\x03\x00\x00")

                    total = -1
                    response = b""
                    servers = []

                    while total == -1 or len(servers) < total:
                        response += await tcpClient.recv()
                        br = BinaryReader(response)

                        # first packet return the total number of servers
                        if total == -1:
                            total = br.read_short()

                        # server bytes length always 127
                        while br.remaining_bytes() >= 127:
                            server = {}
                            server["ip"] = ".".join(
                                map(
                                    str,
                                    reversed(
                                        [
                                            br.read_byte(),
                                            br.read_byte(),
                                            br.read_byte(),
                                            br.read_byte(),
                                        ]
                                    ),
                                )
                            )
                            server["port"] = br.read_short()
                            server["name"] = str(
                                br.read_bytes(100).rstrip(b"\x00"),
                                encoding="utf-8",
                                errors="ignore",
                            )
                            br.read_byte()  # skip
                            server["num_players"] = br.read_byte()
                            server["max_players"] = br.read_byte()
                            server["time"] = br.read_byte()
                            br.read_byte()  # skip
                            server["password"] = ((br.read_byte() >> 1) & 1) == 1
                            br.read_bytes(7)  # skip
                            v = list(
                                reversed(
                                    [
                                        hex(br.read_byte())[2:].rjust(2, "0")
                                        for _ in range(8)
                                    ]
                                )
                            )
                            server[
                                "version"
                            ] = f"{int(v[0], 16)}.{int(v[1], 16)}.{int(v[2] + v[3], 16)}.{int(v[4] + v[5] + v[6] + v[7], 16)}"
                            servers.append(Status(**server))

                        # if the length is less than 127, save the unused bytes for next loop
                        response = br.read()

                return servers
            except TimeoutError:
                pass

        raise Exception("Failed to connect to any of the master servers")


if __name__ == "__main__":
    import asyncio

    async def main_async():
        master_servers = await Scum.query_master_servers()
        print(master_servers)

        scum = Scum(host="15.235.181.19", port=7042, timeout=5.0)
        server = await scum.get_status(master_servers)
        print(server)

    asyncio.run(main_async())
