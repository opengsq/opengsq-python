import abc

from opengsq.models import Server
from opengsq.protocols.socket_async import SocketAsync


class IServer(abc.ABC):
    def __init__(self, address: str, query_port: int):
        super().__init__()
        self.address = SocketAsync.gethostbyname(address)
        self.query_port = query_port

    @property
    @abc.abstractmethod
    def full_name(self):
        pass

    @abc.abstractmethod
    async def query(self) -> Server:
        pass
