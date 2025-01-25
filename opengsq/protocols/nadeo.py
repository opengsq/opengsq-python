from __future__ import annotations

import asyncio
import struct
import xmlrpc.client as xmlrpclib
from typing import Any, Optional

from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.responses.nadeo import Status


class Nadeo(ProtocolBase):
    full_name = "Nadeo GBXRemote Protocol"
    INITIAL_HANDLER = 0x80000000
    MAXIMUM_HANDLER = 0xFFFFFFFF

    def __init__(self, host: str, port: int = 5000, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self.handler = self.MAXIMUM_HANDLER
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        
    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        
        # Read and validate header
        data = await self._reader.read(4)
        header_length = struct.unpack('<I', data)[0]
        
        data = await self._reader.read(header_length)
        header = data.decode()
        
        if header != "GBXRemote 2":
            raise InvalidPacketException('No "GBXRemote 2" header found!')

    async def close(self) -> None:
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def _execute(self, method: str, *args) -> Any:
        if self.handler == self.MAXIMUM_HANDLER:
            self.handler = self.INITIAL_HANDLER
        else:
            self.handler += 1
        
        handler_bytes = self.handler.to_bytes(4, byteorder='little')
        data = xmlrpclib.dumps(args, method).encode()
        packet_len = len(data)
        
        packet = packet_len.to_bytes(4, byteorder='little') + handler_bytes + data
        
        self._writer.write(packet)
        await self._writer.drain()
        
        # Read response
        header = await self._reader.read(8)
        size = struct.unpack('<I', header[:4])[0]
        handler = struct.unpack('<I', header[4:8])[0]
        
        if handler != self.handler:
            raise InvalidPacketException(f'Handler mismatch: {handler} != {self.handler}')
            
        data = await self._reader.readexactly(size)
        
        try:
            response = xmlrpclib.loads(data.decode())
            return response[0][0] if response else None
        except xmlrpclib.Fault as e:
            raise InvalidPacketException(f'RPC Fault: {e}')

    async def authenticate(self, username: str, password: str) -> bool:
        await self.connect()
        result = await self._execute('Authenticate', username, password)
        return bool(result)

    async def get_status(self) -> Status:
        version = await self._execute('GetVersion')
        server_info = await self._execute('GetServerOptions')
        player_list = await self._execute('GetPlayerList', 100, 0)
        current_map = await self._execute('GetCurrentChallengeInfo')  
        
        return Status.from_raw_data(
            version_data=version,
            server_data=server_info,
            players_data=player_list,
            map_data=current_map
        )