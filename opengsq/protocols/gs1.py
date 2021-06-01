import re

from opengsq.interfaces import IProtocol
from opengsq.protocols.binary_reader import BinaryReader
from opengsq.protocols.socket_async import SocketAsync


class GS1(IProtocol):
    full_name = 'Gamespy Query Protocol version 1'

    # Legacy:UT_Server_Query - (https://wiki.beyondunreal.com/Legacy:UT_Server_Query)
    # Query_commands - (https://wiki.beyondunreal.com/XServerQuery#Query_commands)
    class __Request():
        GS1_BASIC = b'\\basic\\'
        GS1_INFO = b'\\info\\xserverquery'
        GS1_RULES = b'\\rules\\xserverquery'
        GS1_PLAYERS = b'\\players\\xserverquery'
        GS1_STATUS = b'\\status\\xserverquery'
        GS1_TEAMS = b'\\teams\\'

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

    async def get_basic(self) -> dict:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_BASIC)
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        return self.__parse_as_key_values(br)

    # Server may still response with Legacy version
    async def get_info(self) -> dict:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_INFO)
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        return self.__parse_as_key_values(br)

    async def get_rules(self) -> list:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_RULES)
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        print(br.read())

        return self.__parse_as_key_values(br)

    async def get_players(self) -> list:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_PLAYERS)
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        return self.__parse_as_object(br)

    async def get_status(self) -> dict:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_STATUS)
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        info = self.__parse_as_key_values(br, is_status=True)
        players = self.__parse_as_object(br)

        status = {}
        status['info'] = info
        status['players'] = players

        return status

    async def get_teams(self) -> list:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_TEAMS)
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        return self.__parse_as_object(br)

    # Legacy versions
    async def get_info_legacy(self) -> dict:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_INFO.replace(b'xserverquery', b''))
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        return self.__parse_as_key_values(br)

    async def get_rules_legacy(self) -> list:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_RULES.replace(b'xserverquery', b''))
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        print(br.read())

        return self.__parse_as_key_values(br)

    async def get_players_legacy(self) -> list:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_PLAYERS.replace(b'xserverquery', b''))
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

        return self.__parse_as_object(br)

    async def get_status_legacy(self) -> dict:
        await self.__connect()
        self.__sock.send(self.__Request.GS1_STATUS.replace(b'xserverquery', b''))
        br = BinaryReader(data=await self.__get_packets_response())
        self.__disconnect()

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
            packet = await self.__sock.recv()

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

    def __parse_as_key_values(self, br: BinaryReader, is_status=False):
        kv = {}

        # Bind key value
        while br.length() > 0:
            key = br.read_string(until=b'\\')

            if is_status and key.lower().startswith('player_'):
                # Read already, so add it back
                br.prepend_bytes(key.encode() + b'\\')
                break

            value = br.read_string(until=b'\\')
            kv[key] = value.strip()

        return kv

    def __parse_as_object(self, br: BinaryReader):
        items = []

        while br.length() > 0:
            # Get the key, for example player_1, frags_1, ping_1, etc...
            key = br.read_string(until=b'\\')

            # Extract to name and index, for example name=player, index=1
            matches = re.search(r'(.+?)_(\d+)', key)
            name = matches.group(1)
            index = int(matches.group(2))

            # Append a dict to items if next index appears
            if len(items) <= index:
                items.append({})

            # Get the value, and strip it since some values contain whitespaces
            value = br.read_string(until=b'\\').strip()

            # Save
            items[index][name] = value

        return items


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        gs1 = GS1(
            address='',
            query_port=7778,
            timeout=5.0
        )
        status = await gs1.get_status()
        print(json.dumps(status, indent=None) + '\n')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()
