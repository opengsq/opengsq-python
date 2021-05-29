from time import time

from opengsq.protocols import A2S
from opengsq.protocols.models import Server


class Mordhau(A2S):
    full_name = 'Mordhau'

    def __init__(self, address: str, query_port: int = 27015, timeout: float = 5.0):
        super().__init__(address=address, query_port=query_port, timeout=timeout, engine=A2S.SOURCE)

    def query(self) -> Server:
        start_time = time()
        info = self.get_info()
        players = self.get_players()
        latency = time() - start_time

        s = Server()
        s.set_from_a2s(info, players)
        s.latency = latency

        # Fix player count
        for sub in str(info['Keywords']).split(','):
            if sub.startswith('B:'):
                s.players = int(sub[2:])
                break

        return s
