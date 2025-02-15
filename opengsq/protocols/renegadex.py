import json
import asyncio
from opengsq.protocol_base import ProtocolBase
from opengsq.responses.renegadex import Status

class RenegadeX(ProtocolBase):
    full_name = "Renegade X Protocol"
    BROADCAST_PORT = 45542

    def __init__(self, host: str, port: int = 7777, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        
    async def get_status(self) -> Status:
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()
        
        class BroadcastProtocol(asyncio.DatagramProtocol):
            def __init__(self, queue, host):
                self.queue = queue
                self.target_host = host
                
            def datagram_received(self, data, addr):
                if addr[0] == self.target_host:
                    self.queue.put_nowait(data)
        
        transport, _ = await loop.create_datagram_endpoint(
            lambda: BroadcastProtocol(queue, self._host),
            local_addr=('0.0.0.0', self.BROADCAST_PORT)
        )
        
        try:
            complete_data = bytearray()
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=self._timeout)
                    complete_data.extend(data)
                    
                    try:
                        json_str = complete_data.decode('utf-8')
                        server_info = json.loads(json_str)
                        return Status.from_dict(server_info)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                        
                except asyncio.TimeoutError:
                    raise TimeoutError("No broadcast received from the specified server")
                    
        finally:
            transport.close()