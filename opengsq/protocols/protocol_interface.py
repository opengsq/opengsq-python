import abc

from opengsq.protocols.models.server import Server


class IProtocol(abc.ABC):    
    @abc.abstractmethod
    def query(self) -> Server:
        pass
