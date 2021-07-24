import abc
from opengsq.socket_async import SocketAsync


class ProtocolBase(abc.ABC):
    @property
    @abc.abstractmethod
    def full_name(self):
        pass

    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        self._sock = None
        self._address = address
        self._query_port = query_port
        self._timeout = timeout

    def __del__(self):
        self._disconnect()

    async def _connect(self):
        self._disconnect()
        self._sock = SocketAsync()
        self._sock.settimeout(self._timeout)
        await self._sock.connect((SocketAsync.gethostbyname(self._address), self._query_port))

    def _disconnect(self):
        if self._sock:
            self._sock.close()
