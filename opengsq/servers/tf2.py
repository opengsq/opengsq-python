from opengsq.protocols import A2S
from opengsq.servers.source import Source


class TF2(Source):
    full_name = 'Team Fortress 2'

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address, query_port, timeout, A2S.SOURCE)
