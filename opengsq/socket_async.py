import asyncio
import socket


class SocketAsync():
    @staticmethod
    def gethostbyname(hostname: str) -> str:
        return socket.gethostbyname(hostname)

    def __init__(self):
        self.__timeout = None
        self.__transport = None
        self.__protocol = None

    def settimeout(self, value: float):
        self.__timeout = value

    async def connect(self, remote_addr):
        loop = asyncio.get_running_loop()
        self.__protocol = self.__Protocol(self.__timeout)

        self.__transport, _ = await loop.create_datagram_endpoint(
            lambda: self.__protocol,
            remote_addr=remote_addr,
        )

    def close(self):
        if self.__transport:
            self.__transport.close()

    def send(self, data: bytes):
        self.__transport.sendto(data)

    async def recv(self) -> bytes:
        return await self.__protocol.recv()

    class __Protocol:
        def __init__(self, timeout: float):
            self.__packets = asyncio.Queue()
            self.__timeout = timeout

        def connection_made(self, transport):
            pass

        def datagram_received(self, data, addr):
            self.__packets.put_nowait((data, addr))

        async def recv(self):
            return (await asyncio.wait_for(self.__packets.get(), timeout=self.__timeout))[0]

        def connection_lost(self, exc):
            pass


if __name__ == '__main__':
    async def test_socket_async():
        socket_async = SocketAsync()
        socket_async.settimeout(5)
        await socket_async.connect(('', 27015))
        socket_async.send(b'\xFF\xFF\xFF\xFFTSource Engine Query\x00\xFF\xFF\xFF\xFF')
        print(await socket_async.recv())
        socket_async.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_socket_async())
    loop.close()
