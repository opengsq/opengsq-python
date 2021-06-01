from opengsq.servers.source import Source


class CSGO(Source):
    full_name = 'Counter-Strike: Global Offensive'

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address, query_port, timeout)
