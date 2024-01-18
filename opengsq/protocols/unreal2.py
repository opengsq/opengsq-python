import re

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Unreal2(ProtocolBase):
    """Unreal 2 Protocol"""
    full_name = 'Unreal 2 Protocol'

    _DETAILS = 0x00
    _RULES = 0x01
    _PLAYERS = 0x02

    async def get_details(self):
        response = await UdpClient.communicate(self, b'\x79\x00\x00\x00' + bytes([self._DETAILS]))

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._DETAILS:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self._DETAILS))
            )

        details = {}
        details['ServerId'] = br.read_long()  # 0
        details['ServerIP'] = br.read_string()  # empty
        details['GamePort'] = br.read_long()
        details['QueryPort'] = br.read_long()  # 0
        details['ServerName'] = self._read_string(br)
        details['MapName'] = self._read_string(br)
        details['GameType'] = self._read_string(br)
        details['NumPlayers'] = br.read_long()
        details['MaxPlayers'] = br.read_long()
        details['Ping'] = br.read_long()
        details['Flags'] = br.read_long()
        details['Skill'] = self._read_string(br)

        return details

    async def get_rules(self):
        response = await UdpClient.communicate(self, b'\x79\x00\x00\x00' + bytes([self._RULES]))

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._RULES:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self._RULES))
            )

        rules = {}
        rules['Mutators'] = []

        while not br.is_end():
            key = self._read_string(br)
            val = self._read_string(br)

            if key.lower() == 'mutator':
                rules['Mutators'].append(val)
            else:
                rules[key] = val

        return rules

    async def get_players(self):
        response = await UdpClient.communicate(self, b'\x79\x00\x00\x00' + bytes([self._PLAYERS]))

        # Remove the first 4 bytes \x80\x00\x00\x00
        br = BinaryReader(response[4:])
        header = br.read_byte()

        if header != self._PLAYERS:
            raise InvalidPacketException(
                'Packet header mismatch. Received: {}. Expected: {}.'
                .format(chr(header), chr(self._PLAYERS))
            )

        players = []

        while not br.is_end():
            player = {}
            player['Id'] = br.read_long()
            player['Name'] = self._read_string(br)
            player['Ping'] = br.read_long()
            player['Score'] = br.read_long()
            player['StatsId'] = br.read_long()
            players.append(player)

        return players

    @staticmethod
    def strip_colors(text: bytes):
        """Strip color codes"""
        return re.compile(b'\x1b...|[\x00-\x1a]').sub(b'', text)

    def _read_string(self, br: BinaryReader):
        length = br.read_byte()
        string = br.read_string()

        if length == len(string) + 1:
            b = bytes(string, encoding='utf-8')
        else:
            b = bytes(string, encoding='utf-16')

        b = Unreal2.strip_colors(b)

        return b.decode('utf-8', 'ignore')


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        # ut2004
        unreal2 = Unreal2(host='109.230.224.189', port=6970, timeout=10.0)
        details = await unreal2.get_details()
        print(json.dumps(details, indent=None) + '\n')
        rules = await unreal2.get_rules()
        print(json.dumps(rules, indent=None) + '\n')
        players = await unreal2.get_players()
        print(json.dumps(players, indent=None) + '\n')

    asyncio.run(main_async())
