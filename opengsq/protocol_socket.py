import asyncio
import socket
from enum import Enum, auto

from opengsq.protocol_base import ProtocolBase


class SocketKind(Enum):
    SOCK_STREAM = auto()
    SOCK_DGRAM = auto()


class Socket():
    @staticmethod
    async def gethostbyname(hostname: str):
        return await asyncio.get_running_loop().run_in_executor(None, socket.gethostbyname, hostname)

    class Protocol(asyncio.Protocol):
        def __init__(self, timeout: float):
            self.__packets = asyncio.Queue()
            self.__timeout = timeout

        async def recv(self):
            return await asyncio.wait_for(self.__packets.get(), timeout=self.__timeout)

        def connection_made(self, transport):
            pass

        def connection_lost(self, exc):
            pass

        def data_received(self, data):
            self.__packets.put_nowait(data)

        def eof_received(self):
            pass

        def datagram_received(self, data, addr):
            self.__packets.put_nowait(data)

        def error_received(self, exc):
            pass

    def __init__(self, kind: SocketKind):
        self.__timeout = None
        self.__transport = None
        self.__protocol = None
        self.__kind = kind
        self.__local_port = None

    def bind_port(self, port: int):
        self.__local_port = port

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def settimeout(self, value: float):
        self.__timeout = value

    async def connect(self, remote_addr):
        await asyncio.wait_for(self.__connect(remote_addr), timeout=self.__timeout)

    async def __connect(self, remote_addr):
        loop = asyncio.get_running_loop()
        self.__protocol = self.__Protocol(self.__timeout)

        if self.__kind == SocketKind.SOCK_STREAM:
            self.__transport, _ = await loop.create_connection(
                lambda: self.__protocol,
                host=remote_addr[0],
                port=remote_addr[1],
                local_addr=('0.0.0.0', self.__local_port) if self.__local_port else None
            )
        else:
            self.__transport, _ = await loop.create_datagram_endpoint(
                lambda: self.__protocol,
                remote_addr=remote_addr,
                local_addr=('0.0.0.0', self.__local_port) if self.__local_port else None
            )

    def close(self):
        if self.__transport:
            self.__transport.close()

    def send(self, data: bytes):
        if self.__kind == SocketKind.SOCK_STREAM:
            self.__transport.write(data)
        else:
            self.__transport.sendto(data)

    async def recv(self, size: int = None) -> bytes:
        if size:
            data = b""
            while len(data) < size:
                chunk = await self.__protocol.recv()
                data += chunk
                if len(data) >= size:
                    return data[:size]
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

        # Streaming Protocols
        def data_received(self, data):
            """Called when some data is received. data is a non-empty bytes object containing the incoming data."""
            self.__packets.put_nowait(data)

        # Streaming Protocols
        def eof_received(self):
            """
            Called when the other end signals it won't send any more data
            (for example by calling transport.write_eof(), if the other end also uses asyncio).
            """
            pass

        # Datagram Protocols
        def datagram_received(self, data, addr):
            """Called when some datagram is received."""
            self.__packets.put_nowait(data)

        # Datagram Protocols
        def error_received(self, exc):
            """Called when a previous send or receive operation raises an OSError. exc is the OSError instance."""
            pass


class UdpClient(Socket):
    @staticmethod
    async def communicate(protocol: ProtocolBase, data: bytes, source_port: int = None):
        with UdpClient() as udpClient:
            if source_port:
                udpClient.bind_port(source_port)
            udpClient.settimeout(protocol._timeout)
            
            loop = asyncio.get_running_loop()
            transport, protocol_instance = await loop.create_datagram_endpoint(
                lambda: Socket.Protocol(protocol._timeout),  # Use public Protocol class
                local_addr=('0.0.0.0', source_port if source_port else 0),
                allow_broadcast=protocol._allow_broadcast
            )
            
            try:
                transport.sendto(data, (protocol._host, protocol._port))
                return await protocol_instance.recv()
            finally:
                transport.close()

    def __init__(self):
        super().__init__(SocketKind.SOCK_DGRAM)


class TcpClient(Socket):
    @staticmethod
    async def communicate(protocol: ProtocolBase, data: bytes):
        with TcpClient() as tcpClient:
            tcpClient.settimeout(protocol._timeout)
            await tcpClient.connect((protocol._host, protocol._port))
            tcpClient.send(data)
            return await tcpClient.recv()

    def __init__(self):
        super().__init__(SocketKind.SOCK_STREAM)


if __name__ == '__main__':
    async def test_socket_async():
        with Socket() as socket_async:
            socket_async.settimeout(5)
            await socket_async.connect(('122.128.109.245', 27015))
            socket_async.send(
                b'\xFF\xFF\xFF\xFFTSource Engine Query\x00\xFF\xFF\xFF\xFF')
            print(await socket_async.recv())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_socket_async())
    loop.close()