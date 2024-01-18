from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_socket import UdpClient
from opengsq.protocols.unreal2 import Unreal2


class KillingFloor(Unreal2):
    """Killing Floor Protocol"""
    full_name = 'Killing Floor Protocol'

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
        details['WaveCurrent'] = br.read_long()
        details['WaveTotal'] = br.read_long()
        details['Ping'] = br.read_long()
        details['Flags'] = br.read_long()
        details['Skill'] = self._read_string(br)

        return details


if __name__ == '__main__':
    import asyncio
    import json

    async def main_async():
        # killingfloor
        killingFloor = KillingFloor(host='185.80.128.168', port=7708, timeout=10.0)
        details = await killingFloor.get_details()
        print(json.dumps(details, indent=None) + '\n')
        rules = await killingFloor.get_rules()
        print(json.dumps(rules, indent=None) + '\n')
        players = await killingFloor.get_players()
        print(json.dumps(players, indent=None) + '\n')

    asyncio.run(main_async())
