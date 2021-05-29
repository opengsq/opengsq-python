from opengsq.protocols import A2S


class CSGO(A2S):
    full_name = 'Counter-Strike: Global Offensive'

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address=address, query_port=query_port, timeout=timeout, engine=A2S.SOURCE)
