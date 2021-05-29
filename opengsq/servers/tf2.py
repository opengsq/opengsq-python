from opengsq.protocols import A2S


class TF2(A2S):
    full_name = 'Team Fortress 2'

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address=address, query_port=query_port, timeout=timeout, engine=A2S.SOURCE)
