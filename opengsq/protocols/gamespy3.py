import re

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class GameSpy3(ProtocolBase):
    """GameSpy Protocol version 3"""
    full_name = 'GameSpy Protocol version 3'
    challenge = False

    async def get_status(self):
        """Retrieves information about the server including, Info, Players, and Teams."""
        # Connect to remote host
        with SocketAsync() as sock:
            sock.settimeout(self._timeout)
            await sock.connect((self._address, self._query_port))

            request_h = b'\xFE\xFD'
            timestamp = b'\x04\x05\x06\x07'
            challenge = b''

            if self.challenge:
                # Packet 1: Initial request - (https://wiki.unrealadmin.org/UT3_query_protocol#Packet_1:_Initial_request)
                sock.send(request_h + b'\x09' + timestamp)

                # Packet 2: First response - (https://wiki.unrealadmin.org/UT3_query_protocol#Packet_2:_First_response)
                response = await sock.recv()

                if response[0] != 9:
                    raise InvalidPacketException(
                        'Packet header mismatch. Received: {}. Expected: {}.'
                        .format(chr(response[0]), chr(9))
                    )

                # Packet 3: Second request - (http://wiki.unrealadmin.org/UT3_query_protocol#Packet_3:_Second_request)
                challenge = int(response[5:].decode('ascii').strip('\x00'))
                challenge = b'' if challenge == 0 else challenge.to_bytes(4, 'big', signed=True)

            request_data = request_h + b'\x00' + timestamp + challenge
            sock.send(request_data + b'\xFF\xFF\xFF\x01')

            # Packet 4: Server information response
            # (http://wiki.unrealadmin.org/UT3_query_protocol#Packet_4:_Server_information_response)
            response = await self.__read(sock)

        br = BinaryReader(response)

        result = {}
        result['info'] = {}

        while True:
            key = br.read_string()

            if key == '':
                break

            result['info'][key] = br.read_string()

        pattern = re.compile(rb'\x00([^a-zA-Z])([a-zA-Z_]+)\x00\x00(.+?(?=\x00\x00))')
        current_id = -1
        current_name = None

        for (id, name, data) in re.findall(pattern, b'\x00' + br.read()):
            values = data.split(b'\x00')
            name = name.decode('utf-8').split('_')[0]

            if current_id != id and id != b'\x00':
                current_id, current_name = id, name
                result[current_name] = [{} for _ in range(len(values))]

            for i in range(len(values)):
                result[current_name][i][name] = values[i].decode('utf-8')

        return result

    async def __read(self, sock) -> bytes:
        packet_count = -1
        payloads = {}

        while packet_count == -1 or len(payloads) > packet_count:
            response = await sock.recv()

            br = BinaryReader(response)
            header = br.read_byte()

            if header != 0:
                raise InvalidPacketException(
                    'Packet header mismatch. Received: {}. Expected: {}.'
                    .format(chr(header), chr(0))
                )

            # Skip the timestamp and splitnum
            br.read_bytes(13)

            # The 'numPackets' byte
            num_packets = br.read_byte()

            # The low 7 bits are the packet index (starting at zero)
            number = num_packets & 0x7F

            # The high bit is whether or not this is the last packet
            if num_packets & 0x80:
                # Set packet_count if it is the last packet
                packet_count = number + 1

            # The object id
            # 0 = server kv information
            # 1 = player_   \x00\x01player_\x00\x00 since \x01
            # 2 = team_t    \x00\x02team_t\x00\x00  since \x02
            # etc...
            obj_id = br.read_byte()
            header = b''

            if obj_id >= 1:
                # The object key name
                string = br.read_string()

                # How many times did the value appear in the previous packet
                count = br.read_byte()

                # Set back the packet header if it didn't appear before
                header = b'\x00' + bytes([obj_id]) + string.encode() + b'\x00\x00' if count == 0 else b''

            payload = header + br.read()[:-1]

            # Remove the last trash string on the payload
            payloads[number] = payload[:payload.rfind(b'\x00') + 1]

        response = b''.join(payloads[number] for number in sorted(payloads))

        return response


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs3 = GameSpy3(address='185.107.96.59', query_port=29900, timeout=5.0)
        server = await gs3.get_status()
        print(json.dumps(server, indent=None))

    asyncio.run(main_async())
