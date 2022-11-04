import json
import re
import struct

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync, SocketKind


class Minecraft(ProtocolBase):
    """Minecraft Protocol (https://wiki.vg/Server_List_Ping)"""
    full_name = 'Minecraft Protocol'

    async def get_status(self, version=47, strip_color=True) -> dict:
        """Get Status

        Args:
            version (int, optional): https://wiki.vg/Protocol_version_numbers. Defaults to 47.
            strip_color (bool, optional): Strip color. Defaults to True.

        Returns:
            dict: status dict
        """

        # Prepare the request
        address = self._address.encode('utf8')
        protocol = self._pack_varint(version)
        request = b'\x00' + protocol + self._pack_varint(len(address)) + address + struct.pack('H', self._query_port) + b'\x01'
        request = self._pack_varint(len(request)) + request + b'\x01\x00'

        with SocketAsync(SocketKind.SOCK_STREAM) as sock:
            sock.settimeout(self._timeout)
            await sock.connect((self._address, self._query_port))
            sock.send(request)

            response = await sock.recv()
            br = BinaryReader(response)
            length = self._unpack_varint(br)

            # Keep recv() until reach packet length
            while len(response) < length:
                response += await sock.recv()

        # Read fill response
        br = BinaryReader(response)
        self._unpack_varint(br)  # packet length
        self._unpack_varint(br)  # packet id
        self._unpack_varint(br)  # json length

        data = json.loads(br.read().decode('utf-8'))

        if strip_color:
            if 'sample' in data['players']:
                for i, player in enumerate(data['players']['sample']):
                    data['players']['sample'][i]['name'] = Minecraft.strip_colors(player['name'])

            if isinstance(data['description'], str):
                data['description'] = Minecraft.strip_colors(data['description'])

            if 'text' in data['description'] and isinstance(data['description']['text'], str):
                data['description']['text'] = Minecraft.strip_colors(data['description']['text'])

            if 'extra' in data['description'] and isinstance(data['description']['extra'], list):
                for i, extra in enumerate(data['description']['extra']):
                    if isinstance(extra['text'], str):
                        data['description']['extra'][i]['text'] = Minecraft.strip_colors(extra['text'])

        return data

    async def get_status_pre17(self, strip_color=True) -> dict:
        """Get ping info from a server that uses a version older than Minecraft 1.7"""
        with SocketAsync(SocketKind.SOCK_STREAM) as sock:
            sock.settimeout(self._timeout)
            await sock.connect((self._address, self._query_port))
            sock.send(b'\xFE\x01')
            response = await sock.recv()

        br = BinaryReader(response)
        header = br.read_byte()

        if header != 0xFF:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(0xFF))
            )

        br.read_bytes(2)  # length of the following string
        items = br.read().split(b'\x00\x00')

        result = {}
        result['protocol'] = str(items[1], 'utf-16be')
        result['version'] = str(items[2], 'utf-16be')
        result['motd'] = str(items[3], 'utf-16be')
        result['numplayers'] = int(str(items[4], 'utf-16be'))
        result['maxplayers'] = int(str(items[5], 'utf-16be'))

        if strip_color:
            result['motd'] = Minecraft.strip_colors(result['motd'])

        return result

    @staticmethod
    def strip_colors(text: str):
        """Strip color codes"""
        return re.compile(r'\u00A7[0-9A-FK-OR]', re.IGNORECASE).sub('', text)

    def _pack_varint(self, val: int):
        total = b''

        if val < 0:
            val = (1 << 32) + val

        while val >= 0x80:
            bits = val & 0x7F
            val >>= 7
            total += struct.pack('B', (0x80 | bits))

        bits = val & 0x7F
        total += struct.pack('B', bits)

        return total

    def _unpack_varint(self, br: BinaryReader):
        total = 0
        shift = 0
        val = 0x80

        while val & 0x80:
            val = struct.unpack('B', br.read_bytes(1))[0]
            total |= ((val & 0x7F) << shift)
            shift += 7

        if total & (1 << 31):
            total -= (1 << 32)

        return total


if __name__ == '__main__':
    import asyncio

    async def main_async():
        minecraft = Minecraft(address='51.83.219.117', query_port=25565, timeout=5.0)
        status = await minecraft.get_status(47, strip_color=True)
        print(json.dumps(status, indent=None, ensure_ascii=False) + '\n')
        status = await minecraft.get_status_pre17()
        print(json.dumps(status, indent=None, ensure_ascii=False) + '\n')

    asyncio.run(main_async())
