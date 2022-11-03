from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.socket_async import SocketAsync


class Raknet(ProtocolBase):
    """Raknet Protocol (https://wiki.vg/Raknet_Protocol)"""
    full_name = 'Raknet Protocol'

    __ID_UNCONNECTED_PING = b'\x01'
    __ID_UNCONNECTED_PONG = b'\x1C'
    __TIMESTAMP = b'\x12\x23\x34\x45\x56\x67\x78\x89'
    __OFFLINE_MESSAGE_DATA_ID = b'\x00\xFF\xFF\x00\xFE\xFE\xFE\xFE\xFD\xFD\xFD\xFD\x12\x34\x56\x78'
    __CLIENT_GUID = b'\x00\x00\x00\x00\x00\x00\x00\x00'

    async def get_status(self) -> dict:
        request = self.__ID_UNCONNECTED_PING + self.__TIMESTAMP + self.__OFFLINE_MESSAGE_DATA_ID + self.__CLIENT_GUID
        response = await SocketAsync.send_and_receive(self._address, self._query_port, self._timeout, request)

        br = BinaryReader(response)
        header = br.read_bytes(1)

        if header != self.__ID_UNCONNECTED_PONG:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(header, self.__ID_UNCONNECTED_PONG)
            )

        br.read_bytes(len(self.__TIMESTAMP) + len(self.__CLIENT_GUID))  # skip timestamp and guid
        magic = br.read_bytes(len(self.__OFFLINE_MESSAGE_DATA_ID))

        if magic != self.__OFFLINE_MESSAGE_DATA_ID:
            raise InvalidPacketException(
                'Magic value mismatch. Received: {}. Expected: {}.'
                .format(magic, self.__OFFLINE_MESSAGE_DATA_ID)
            )

        br.read_short()  # skip remaining packet length

        d = [b';']  # delimiter
        result = {}
        result['edition'] = br.read_string(d)
        result['motd_line_1'] = br.read_string(d)
        result['protocol_version'] = int(br.read_string(d))
        result['version'] = br.read_string(d)
        result['num_players'] = int(br.read_string(d))
        result['max_players'] = int(br.read_string(d))

        # Try to read all data
        try:
            result['server_uid'] = br.read_string(d)
            result['motd_line_2'] = br.read_string(d)
            result['gamemode'] = br.read_string(d)
            result['gamemode_numeric'] = int(br.read_string(d))
            result['port_ipv4'] = int(br.read_string(d))
            result['port_ipv6'] = int(br.read_string(d))
        except Exception:
            pass

        return result


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        raknet = Raknet(address='193.70.94.83', query_port=19132, timeout=5.0)
        status = await raknet.get_status()
        print(json.dumps(status, indent=None) + '\n')

    asyncio.run(main_async())
