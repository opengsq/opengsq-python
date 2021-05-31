import abc


class IProtocol(abc.ABC):
    @property
    @abc.abstractmethod
    def full_name(self):
        pass
