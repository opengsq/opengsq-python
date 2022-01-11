import asyncio
import socket
from enum import Enum, auto


class SocketAsync():
    class SocketKind(Enum):
        SOCK_STREAM = auto() 
        SOCK_DGRAM = auto()
    
    @staticmethod
    def gethostbyname(hostname: str) -> str:
        return socket.gethostbyname(hostname)

    def __init__(self, kind: SocketKind = SocketKind.SOCK_DGRAM):
        self.__timeout = None
        self.__transport = None
        self.__protocol = None
        self.__kind = kind

    def settimeout(self, value: float):
        self.__timeout = value

    async def connect(self, remote_addr):
        loop = asyncio.get_running_loop()
        self.__protocol = self.__Protocol(self.__timeout)

        if self.__kind == self.SocketKind.SOCK_STREAM:
            self.__transport, _ = await loop.create_connection(
                lambda: self.__protocol,
                host=remote_addr[0],
                port=remote_addr[1],
            )
        else:
            self.__transport, _ = await loop.create_datagram_endpoint(
                lambda: self.__protocol,
                remote_addr=remote_addr,
            )

    def close(self):
        if self.__transport:
            self.__transport.close()

    def send(self, data: bytes):
        if self.__kind == self.SocketKind.SOCK_STREAM:
            self.__transport.write(data)
        else:
            self.__transport.sendto(data)

    async def recv(self) -> bytes:
        return await self.__protocol.recv()

    class __Protocol(asyncio.Protocol):
        def __init__(self, timeout: float):
            self.__packets = asyncio.Queue()
            self.__timeout = timeout

        async def recv(self):
            return await asyncio.wait_for(self.__packets.get(), timeout=self.__timeout)

        def connection_made(self, transport):
            pass
        
        def connection_lost(self, exc):
            pass
        
        # SOCK_STREAM
        def data_received(self, data):
            self.__packets.put_nowait(data)
        
        # SOCK_STREAM
        def eof_received(self):
            pass

        # SOCK_DGRAM
        def datagram_received(self, data, addr):
            self.__packets.put_nowait(data)
        

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
