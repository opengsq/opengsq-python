import struct

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class Satisfactory(ProtocolBase):
    """Satisfactory Protocol"""
    full_name = 'Satisfactory Protocol'

    async def get_status(self) -> dict:
        """
        Retrieves information about the server including state, version, and beacon port
        Server state: 1 - Idle (no game loaded), 2 - currently loading or creating a game, 3 - currently in game
        """
        # Credit: https://github.com/dopeghoti/SF-Tools/blob/main/Protocol.md

        # Send message id, protocol version
        request = struct.pack('2b', 0, 0) + 'opengsq'.encode()
        response = await SocketAsync.send_and_receive(self._host, self._port, self._timeout, request)
        br = BinaryReader(response)
        header = br.read_byte()

        if header != 1:
            raise InvalidPacketException('Packet header mismatch. Received: {}. Expected: {}.'.format(chr(header), chr(1)))

        br.read_byte()  # Protocol version
        br.read_bytes(8)  # Request data

        result = {}
        result['State'] = br.read_byte()
        result['Version'] = br.read_long()
        result['BeaconPort'] = br.read_short()

        return result


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        satisfactory = Satisfactory(host='delta3.ptse.host', port=15777, timeout=5.0)
        status = await satisfactory.get_status()
        print(json.dumps(status, indent=None) + '\n')

    asyncio.run(main_async())
