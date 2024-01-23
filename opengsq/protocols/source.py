import bz2
import zlib

from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Source(ProtocolBase):
    """Source Engine Protocol"""

    full_name = "Source Engine Protocol"

    _A2S_INFO = b"\x54Source Engine Query\0"
    _A2S_PLAYER = b"\x55"
    _A2S_RULES = b"\x56"

    class __RequestHeader:
        A2A_PING = b"\x69"
        A2S_SERVERQUERY_GETCHALLENGE = b"\x57"

    class __ResponseHeader:
        S2C_CHALLENGE = 0x41
        S2A_INFO_SRC = 0x49
        S2A_INFO_DETAILED = 0x6D
        S2A_PLAYER = 0x44
        S2A_RULES = 0x45
        A2A_ACK = 0x6A

    async def get_info(self) -> dict:
        """
        Retrieves information about the server including,
        but not limited to: its name, the map currently being played, and the number of players.

        See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_INFO
        """
        response_data = await self.__connect_and_send_challenge(self._A2S_INFO)

        br = BinaryReader(response_data)
        header = br.read_byte()

        if (
            header != self.__ResponseHeader.S2A_INFO_SRC
            and header != self.__ResponseHeader.S2A_INFO_DETAILED
        ):
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {} or {}.".format(
                    chr(header),
                    chr(self.__ResponseHeader.S2A_INFO_SRC),
                    chr(self.__ResponseHeader.S2A_INFO_DETAILED),
                )
            )

        if header == self.__ResponseHeader.S2A_INFO_SRC:
            return self.__parse_from_info_src(br)

        # Obsolete GoldSource Response
        return self.__parse_from_info_detailed(br)

    def __parse_from_info_src(self, br: BinaryReader) -> dict:
        info = {}
        info["Protocol"] = br.read_byte()
        info["Name"] = br.read_string()
        info["Map"] = br.read_string()
        info["Folder"] = br.read_string()
        info["Game"] = br.read_string()
        info["ID"] = br.read_short()
        info["Players"] = br.read_byte()
        info["MaxPlayers"] = br.read_byte()
        info["Bots"] = br.read_byte()
        info["ServerType"] = chr(br.read_byte())
        info["Environment"] = chr(br.read_byte())
        info["Visibility"] = br.read_byte()
        info["VAC"] = br.read_byte()

        # These fields only exist in a response if the server is running The Ship
        if info["ID"] == 2400:
            info["Mode"] = br.read_byte()
            info["Witnesses"] = br.read_byte()
            info["Duration"] = br.read_byte()

        info["Version"] = br.read_string()
        info["EDF"] = br.read_byte()

        if info["EDF"] & 0x80:
            info["GamePort"] = br.read_short()

        if info["EDF"] & 0x10:
            info["SteamID"] = br.read_long_long()

        if info["EDF"] & 0x40:
            info["SpecPort"] = br.read_short()
            info["SpecName"] = br.read_string()

        if info["EDF"] & 0x20:
            info["Keywords"] = br.read_string()

        if info["EDF"] & 0x01:
            info["GameID"] = br.read_long_long()

        return info

    def __parse_from_info_detailed(self, br: BinaryReader) -> dict:
        info = {}
        info["Address"] = br.read_string()
        info["Name"] = br.read_string()
        info["Map"] = br.read_string()
        info["Folder"] = br.read_string()
        info["Game"] = br.read_string()
        info["Players"] = br.read_byte()
        info["MaxPlayers"] = br.read_byte()
        info["Protocol"] = br.read_byte()
        info["ServerType"] = chr(br.read_byte())
        info["Environment"] = chr(br.read_byte())
        info["Visibility"] = br.read_byte()
        info["Mod"] = br.read_byte()

        if info["Mod"] == 1:
            info["Link"] = br.read_string()
            info["DownloadLink"] = br.read_string()

            br.read_byte()

            info["Version"] = br.read_long()
            info["Size"] = br.read_long()
            info["Type"] = br.read_byte()
            info["DLL"] = br.read_byte()

        info["VAC"] = br.read_byte()
        info["Bots"] = br.read_byte()

        return info

    async def get_players(self) -> list:
        """
        This query retrieves information about the players currently on the server.

        See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_PLAYER
        """
        response_data = await self.__connect_and_send_challenge(self._A2S_PLAYER)

        br = BinaryReader(response_data)
        header = br.read_byte()

        if header != self.__ResponseHeader.S2A_PLAYER:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(self.__ResponseHeader.S2A_PLAYER)
                )
            )

        player_count = br.read_byte()
        players = []

        for _ in range(player_count):
            br.read_byte()

            player = {}
            player["Name"] = br.read_string()
            player["Score"] = br.read_long()
            player["Duration"] = br.read_float()
            players.append(player)

        if br.remaining_bytes() > 0:
            for i in range(player_count):
                players[i]["Deaths"] = br.read_long()
                players[i]["Money"] = br.read_long()

        return players

    async def get_rules(self) -> dict:
        """
        Returns the server rules, or configuration variables in name/value pairs.

        See: https://developer.valvesoftware.com/wiki/Server_queries#A2S_RULES
        """
        response_data = await self.__connect_and_send_challenge(self._A2S_RULES)

        br = BinaryReader(response_data)
        header = br.read_byte()

        if header != self.__ResponseHeader.S2A_RULES:
            raise InvalidPacketException(
                "Packet header mismatch. Received: {}. Expected: {}.".format(
                    chr(header), chr(self.__ResponseHeader.S2A_RULES)
                )
            )

        rule_count = br.read_short()
        rules = dict((br.read_string(), br.read_string()) for _ in range(rule_count))

        return rules

    async def __connect_and_send_challenge(self, header: __RequestHeader) -> bytes:
        # Connect to remote host
        with UdpClient() as udpClient:
            udpClient.settimeout(self._timeout)
            await udpClient.connect((self._host, self._port))

            # Send and receive
            request_base = b"\xFF\xFF\xFF\xFF" + header
            request_data = request_base

            if header != self._A2S_INFO:
                request_data += b"\xFF\xFF\xFF\xFF"

            udpClient.send(request_data)

            # Retries 3 times, some servers require multiple challenges
            for _ in range(3):
                response_data = await self.__receive(udpClient)
                br = BinaryReader(response_data)
                header = br.read_byte()

                # The server response with a challenge
                if header == self.__ResponseHeader.S2C_CHALLENGE:
                    challenge = br.read()

                    # Send the challenge and receive
                    udpClient.send(request_base + challenge)
                else:
                    break

        return response_data

    async def __receive(self, udpClient: UdpClient) -> bytes:
        total_packets = -1
        payloads = dict()
        packets = list()

        while True:
            response_data = await udpClient.recv()
            packets.append(response_data)

            br = BinaryReader(response_data)
            header = br.read_long()

            # Simple Response Format
            if header == -1:
                # Return the payload
                return br.read()

            # Packet id
            id = br.read_long()
            is_compressed = (id & 0x80000000) < 0

            # Check is GoldSource multi-packet response format
            if self.__is_gold_source_split(BinaryReader(br.read())):
                return await self.__parse_gold_source_packet(udpClient, packets)

            # The total number of packets
            total_packets = br.read_byte()

            # The number of the packet
            number = br.read_byte()

            # Packet size
            br.read_short()

            if number == 0 and is_compressed:
                # Decompressed size
                br.read_long()

                # CRC32 sum
                crc32_checksum = br.read_long()

            payloads[number] = br.read()

            if total_packets == -1 or len(payloads) < total_packets:
                continue

            break

        # Combine the payloads
        combined_payload = b"".join(payloads[number] for number in sorted(payloads))

        # Decompress the payload
        if is_compressed:
            combined_payload = bz2.decompress(combined_payload)

            # Check CRC32 sum
            if zlib.crc32(combined_payload) != crc32_checksum:
                raise InvalidPacketException(
                    "CRC32 checksum mismatch of uncompressed packet data."
                )

        return (
            combined_payload.startswith(b"\xFF\xFF\xFF\xFF")
            and combined_payload[4:]
            or combined_payload
        )

    def __is_gold_source_split(self, br: BinaryReader):
        # Upper 4 bits represent the number of the current packet (starting at 0)
        number = br.read_byte() >> 4

        # Check is it Gold Source packet split format
        return number == 0 and br.read().startswith(b"\xFF\xFF\xFF\xFF")

    async def __parse_gold_source_packet(self, udpClient: UdpClient, packets: list):
        total_packets = -1
        payloads = dict()

        while total_packets == -1 or len(payloads) < total_packets:
            # Load the old received packets first, then receive the packets
            if len(payloads) < len(packets):
                response_data = packets[len(payloads)]
            else:
                response_data = await udpClient.recv()

            br = BinaryReader(response_data)

            # Header
            br.read_long()

            # Packet id
            br.read_long()

            # The total number of packets
            total_packets = br.read_byte()

            # Upper 4 bits represent the number of the current packet (starting at 0)
            number = total_packets >> 4

            # Bottom 4 bits represent the total number of packets (2 to 15)
            total_packets &= 0x0F

            payloads[number] = br.read()

        # Combine the payloads
        combined_payload = b"".join(payloads[number] for number in sorted(payloads))

        return (
            combined_payload.startswith(b"\xFF\xFF\xFF\xFF")
            and combined_payload[4:]
            or combined_payload
        )


if __name__ == "__main__":
    import asyncio
    import json

    async def main_async():
        source = Source(host="209.205.114.187", port=27015, timeout=5.0)
        info = await source.get_info()
        print(json.dumps(info, indent=None, ensure_ascii=False) + "\n")
        players = await source.get_players()
        print(json.dumps(players, indent=None, ensure_ascii=False) + "\n")
        rules = await source.get_rules()
        print(json.dumps(rules, indent=None, ensure_ascii=False) + "\n")

    asyncio.run(main_async())
