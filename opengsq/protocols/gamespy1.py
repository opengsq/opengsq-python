import re

from opengsq.binary_reader import BinaryReader
from opengsq.protocol_base import ProtocolBase


class GameSpy1(ProtocolBase):
    full_name = 'GameSpy Query Protocol version 1'

    # Legacy:UT_Server_Query - (https://wiki.beyondunreal.com/Legacy:UT_Server_Query)
    # Query_commands - (https://wiki.beyondunreal.com/XServerQuery#Query_commands)
    class __Request():
        BASIC = b'\\basic\\'
        INFO = b'\\info\\xserverquery'
        RULES = b'\\rules\\xserverquery'
        PLAYERS = b'\\players\\xserverquery'
        STATUS = b'\\status\\xserverquery'
        TEAMS = b'\\teams\\'

    def __init__(self, address: str, query_port: int, timeout: float = 5.0):
        super().__init__(address, query_port, timeout)

    async def get_basic(self) -> dict:
        return self.__parse_as_key_values(await self.__connect_and_send(self.__Request.BASIC))

    # Server may still response with Legacy version
    async def get_info(self) -> dict:
        return self.__parse_as_key_values(await self.__connect_and_send(self.__Request.INFO))

    async def get_rules(self) -> list:
        return self.__parse_as_key_values(await self.__connect_and_send(self.__Request.RULES))

    async def get_players(self) -> list:
        return self.__parse_as_object(await self.__connect_and_send(self.__Request.PLAYERS))

    async def get_status(self) -> dict:
        br = await self.__connect_and_send(self.__Request.STATUS)

        info = self.__parse_as_key_values(br, is_status=True)
        players = self.__parse_as_object(br)

        status = {}
        status['info'] = info
        status['players'] = players

        return status

    async def get_teams(self) -> list:
        return self.__parse_as_object(await self.__connect_and_send(self.__Request.TEAMS))

    # Legacy versions
    async def get_info_legacy(self) -> dict:
        return self.__parse_as_key_values(await self.__connect_and_send(self.__Request.INFO.replace(b'xserverquery', b'')))

    async def get_rules_legacy(self) -> list:
        return self.__parse_as_key_values(await self.__connect_and_send(self.__Request.RULES.replace(b'xserverquery', b'')))

    async def get_players_legacy(self) -> list:
        return self.__parse_as_object(await self.__connect_and_send(self.__Request.PLAYERS.replace(b'xserverquery', b'')))

    async def get_status_legacy(self) -> dict:
        br = await self.__connect_and_send(self.__Request.STATUS.replace(b'xserverquery', b''))

        info = self.__parse_as_key_values(br, is_status=True)
        players = self.__parse_as_object(br)

        status = {}
        status['info'] = info
        status['players'] = players

        return status

    # Receive packets and sort it
    async def __get_packets_response(self):
        payloads = {}
        packet_count = -1

        # Loop until received all packets
        while packet_count == -1 or len(payloads) < packet_count:
            packet = await self._sock.recv()

            # If it is the last packet, it will contain b'\\final\\' at the end of the response
            if packet.rsplit(b'\\', 2)[1] == b'final':
                # Split to payload, "queryid", query_id
                payload, _, query_id = packet[:-7].rsplit(b'\\', 2)

                # Get the packet number from query_id
                number = re.search(rb'\d+.(\d+)', query_id).group(1)

                # Save the packet count
                packet_count = int(number)
            else:
                # Split to payload, "queryid", query_id
                payload, _, query_id = packet.rsplit(b'\\', 2)

                # Get the packet number from query_id
                number = re.search(rb'\d+.(\d+)', query_id).group(1)

            # Save the payload, remove the first byte if it is the first packet
            payloads[number] = int(number) == 1 and payload[1:] or payload

        # Sort the payload and return as bytes
        response = b''.join(payloads[number] for number in sorted(payloads))

        return response

    async def __connect_and_send(self, data) -> BinaryReader:
        await self._connect()

        self._sock.send(data)
        br = BinaryReader(await self.__get_packets_response())

        self._disconnect()

        return br

    def __parse_as_key_values(self, br: BinaryReader, is_status=False):
        kv = {}

        # Bind key value
        while br.length() > 0:
            key = br.read_string(b'\\')

            if is_status and key.lower().startswith('player_'):
                # Read already, so add it back
                br.prepend_bytes(key.encode() + b'\\')
                break

            value = br.read_string(b'\\')
            kv[key] = value.strip()

        return kv

    def __parse_as_object(self, br: BinaryReader):
        items = []

        while br.length() > 0:
            # Get the key, for example player_1, frags_1, ping_1, etc...
            key = br.read_string(b'\\')

            # Extract to name and index, for example name=player, index=1
            matches = re.search(r'(.+?)_(\d+)', key)
            name = matches.group(1)
            index = int(matches.group(2))

            # Append a dict to items if next index appears
            if len(items) <= index:
                items.append({})

            # Get the value, and strip it since some values contain whitespaces
            value = br.read_string(b'\\').strip()

            # Save
            items[index][name] = value

        return items


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs1 = GameSpy1(
            address='139.162.235.20',
            query_port=7778,
            timeout=5.0
        )
        status = await gs1.get_status()
        print(json.dumps(status, indent=None) + '\n')

    asyncio.run(main_async())