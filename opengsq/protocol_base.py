import abc


class ProtocolBase(abc.ABC):
    @property
    @abc.abstractmethod
    def full_name(self) -> str:
        pass

    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self._host = host
        self._port = port
        self._timeout = timeout
