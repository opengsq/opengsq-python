from __future__ import annotations

import bz2
import zlib

from opengsq.responses.source import (
    Environment,
    ExtraDataFlag,
    GoldSourceInfo,
    PartialInfo,
    Player,
    ServerType,
    SourceInfo,
    VAC,
    Visibility,
)
from opengsq.binary_reader import BinaryReader
from opengsq.exceptions import InvalidPacketException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient


class Source(ProtocolBase):
    """
    This class represents the Source Engine Protocol. It provides methods to interact with the Source Engine API.
    """

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

    async def get_info(self) -> PartialInfo:
        """
        Asynchronously retrieves information about the server including, but not limited to: its name, the map currently being played, and the number of players.

        :return: A PartialInfo object containing the information about the server.
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

    def __parse_from_info_src(self, br: BinaryReader) -> SourceInfo:
        """
        Parses the information from the given BinaryReader object.

        :param br: The BinaryReader object to parse the information from.
        :return: A SourceInfo object containing the parsed information.
        """
        info = {}
        info["protocol"] = br.read_byte()
        info["name"] = br.read_string()
        info["map"] = br.read_string()
        info["folder"] = br.read_string()
        info["game"] = br.read_string()
        info["id"] = br.read_short()
        info["players"] = br.read_byte()
        info["max_players"] = br.read_byte()
        info["bots"] = br.read_byte()
        info["server_type"] = ServerType(br.read_byte())
        info["environment"] = Environment(br.read_byte())
        info["visibility"] = Visibility(br.read_byte())
        info["vac"] = VAC(br.read_byte())

        # These fields only exist in a response if the server is running The Ship
        if info["id"] == 2400:
            info["mode"] = br.read_byte()
            info["witnesses"] = br.read_byte()
            info["duration"] = br.read_byte()

        info["version"] = br.read_string()
        edf = ExtraDataFlag(br.read_byte())
        info["edf"] = edf

        if edf.has_flag(ExtraDataFlag.Port):
            info["port"] = br.read_short()

        if edf.has_flag(ExtraDataFlag.SteamID):
            info["steam_id"] = br.read_long_long()

        if edf.has_flag(ExtraDataFlag.Spectator):
            info["spectator_port"] = br.read_short()
            info["spectator_name"] = br.read_string()

        if edf.has_flag(ExtraDataFlag.Keywords):
            info["keywords"] = br.read_string()

        if edf.has_flag(ExtraDataFlag.GameID):
            info["game_id"] = br.read_long_long()

        return SourceInfo(**info)

    def __parse_from_info_detailed(self, br: BinaryReader) -> GoldSourceInfo:
        """
        Parses the information from the given BinaryReader object.

        :param br: The BinaryReader object to parse the information from.
        :return: A GoldSourceInfo object containing the parsed information.
        """
        info = {}
        info["address"] = br.read_string()
        info["name"] = br.read_string()
        info["map"] = br.read_string()
        info["folder"] = br.read_string()
        info["game"] = br.read_string()
        info["players"] = br.read_byte()
        info["max_players"] = br.read_byte()
        info["protocol"] = br.read_byte()
        info["server_type"] = ServerType(br.read_byte())
        info["environment"] = Environment(br.read_byte())
        info["visibility"] = Visibility(br.read_byte())
        info["mod"] = br.read_byte()

        if info["mod"] == 1:
            info["link"] = br.read_string()
            info["download_link"] = br.read_string()

            br.read_byte()

            info["version"] = br.read_long()
            info["size"] = br.read_long()
            info["type"] = br.read_byte()
            info["dll"] = br.read_byte()

        info["vac"] = VAC(br.read_byte())
        info["bots"] = br.read_byte()

        return GoldSourceInfo(**info)

    async def get_players(self) -> list[Player]:
        """
        Asynchronously retrieves information about the players currently on the server.

        :return: A list of Player objects containing the information about the players.
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
            player["name"] = br.read_string()
            player["score"] = br.read_long()
            player["duration"] = br.read_float()
            players.append(player)

        if br.remaining_bytes() > 0:
            for i in range(player_count):
                players[i]["deaths"] = br.read_long()
                players[i]["money"] = br.read_long()

        return [Player(**player) for player in players]

    async def get_rules(self) -> dict[str, str]:
        """
        Asynchronously retrieves the rules of the game server, or configuration variables in name/value pairs.

        :return: A dictionary containing the rules of the game server.
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
        """
        Asynchronously connects to the game server and sends the given header.

        :param header: The header to send to the game server.
        :return: The response from the game server.
        """
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

    async def main_async():
        source = Source(host="45.62.160.71", port=27015, timeout=5.0)
        info = await source.get_info()
        print(info)

        await asyncio.sleep(1)
        players = await source.get_players()
        print(players)

        await asyncio.sleep(1)
        rules = await source.get_rules()
        print(rules)

    asyncio.run(main_async())
