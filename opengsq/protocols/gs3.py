import asyncio
import re

from opengsq.interfaces import IProtocol
from opengsq.protocols.binary_reader import BinaryReader
from opengsq.protocols.socket_async import SocketAsync


class GS3(IProtocol):
    full_name = 'Gamespy Query Protocol version 3'
    challenge = False

    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        self.__sock = None
        self.__address = address
        self.__query_port = query_port
        self.__timeout = timeout

    def __del__(self):
        self.__disconnect()

    async def __connect(self):
        self.__disconnect()
        self.__sock = SocketAsync()
        self.__sock.settimeout(self.__timeout)
        await self.__sock.connect((SocketAsync.gethostbyname(self.__address), self.__query_port))

    def __disconnect(self):
        if self.__sock:
            self.__sock.close()

    async def get_info(self):
        await self.__connect()

        request_h = b'\xFE\xFD'
        timestamp = b'\x04\x05\x06\x07'
        challenge = b''

        if self.challenge:
            # Packet 1: Initial request - (https://wiki.unrealadmin.org/UT3_query_protocol#Packet_1:_Initial_request)
            self.__sock.send(request_h + b'\x09' + timestamp)

            # Packet 2: First response - (https://wiki.unrealadmin.org/UT3_query_protocol#Packet_2:_First_response)
            response = await self.__sock.recv()

            if response[0] != 9:
                raise InvalidPacketException(
                    'Packet header mismatch. Received: {}. Expected: {}.'
                    .format(chr(response[0]), chr(9))
                )

            # Packet 3: Second request - (http://wiki.unrealadmin.org/UT3_query_protocol#Packet_3:_Second_request)
            challenge = int(response[5:].decode('ascii').strip('\x00'))
            challenge = b'' if challenge == 0 else challenge.to_bytes(4, 'big', signed=True)

        request_data = request_h + b'\x00' + timestamp + challenge
        self.__sock.send(request_data + b'\xFF\xFF\xFF\x01')

        # Packet 4: Server information response - (http://wiki.unrealadmin.org/UT3_query_protocol#Packet_4:_Server_information_response)
        response = await self.__read()

        br = BinaryReader(data=response)

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
            name = name.decode('utf-8')

            if current_id != id and id != b'\x00':
                current_id, current_name = id, name
                result[current_name] = [{} for _ in range(len(values))]
            
            for i in range(len(values)):
                result[current_name][i][name] = values[i].decode('utf-8')

        return result

    async def __read(self) -> bytes:
        packet_count = -1
        payloads = {}

        while packet_count == -1 or len(payloads) > packet_count:
            response = await self.__sock.recv()

            br = BinaryReader(data=response)
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


class InvalidPacketException(Exception):
    pass


if __name__ == '__main__':
    import json

    async def main_async():
        ut3 = GS3(address='', query_port=29900, timeout=5.0)
        server = await ut3.get_info()
        print(json.dumps(server, indent=None))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()
