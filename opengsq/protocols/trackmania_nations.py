"""
TrackMania Nations/United Forever (TmForever) native server query.

The query uses the game's own TCP protocol on the game port (default 2350), the
same way the game client fetches the details shown in its server browser.
Reverse-engineered from TrackmaniaServer.exe (2011-02-21).

All integers are little-endian.

TCP framing::

    u32 length | message[length]

Message (CNetNod)::

    u8  flags     0x80 | 0x01 compressed | 0x02 checksum | 0x04/0x08 sequenced
    u8  type      0x03 = CNetFormConnectionAdmin (class 0x12010000)
    u16 sequence  only if flags & 0x0C
    u32 checksum  only if flags & 0x02: sum of the four u32 words of
                  HMAC-MD5(_CHECKSUM_KEY, message with the checksum zeroed)
    payload       if flags & 0x01: u32 uncompressed size + LZO1X stream

CNetFormConnectionAdmin payload (the checksum is mandatory)::

    u32 version   must be 7, otherwise the server answers "Please upgrade"
    u32 subtype   8: switch the connection into query mode (no payload)
                  7: u32 request_id                         (client -> server)
                  6: u32 request_id | u32 size | u8[size]   (server -> client)

The subtype 6 data is the server info (CTrackManiaNetworkServerInfo), see
TrackmaniaNations.parse_server_info. str is u32 length + bytes, wstr the same
with UTF-8 (prefixed by a BOM if it contains non-ASCII characters).
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import struct
from typing import ClassVar

from opengsq.exceptions import InvalidPacketException, ServerNotFoundException
from opengsq.protocol_base import ProtocolBase
from opengsq.responses.trackmania_nations import Challenge, Player, ServerInfo


class TrackmaniaNations(ProtocolBase):
    """
    Trackmania Nations Protocol Implementation
    """

    @property
    def full_name(self) -> str:
        return "Trackmania Nations Protocol"

    DEFAULT_PORT = 2350

    GAME_MODES: ClassVar[dict[int, str]] = {
        1: "TimeAttack",
        3: "Rounds",
        6: "Team",
        7: "Laps",
        8: "Stunts",
        9: "Cup",
    }

    _FLAG_COMPRESSED = 0x01
    _FLAG_CHECKSUM = 0x02
    _FLAG_SEQUENCE = 0x0C

    _MESSAGE_CONNECTION_ADMIN = 0x03
    _CONNECTION_ADMIN_VERSION = 7
    _SUBTYPE_REFUSED = 1
    _SUBTYPE_INFO = 6
    _SUBTYPE_INFO_REQUEST = 7
    _SUBTYPE_QUERY_MODE = 8

    # Request id the server puts into the reply when it has no game info yet.
    _NO_INFO = 0xFFFFFFFF

    _CHECKSUM_KEY = struct.pack("<4I", 0x80D79DB8, 0xBA216B72, 0x15439598, 0xE1EC1CFA)
    _MAX_MESSAGE_SIZE = 0x100000

    # First byte of the server info: high bits 001 = valid, low bits = game.
    _GAME_TAG_TRACKMANIA = 0x0D

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)

    async def get_info(self) -> ServerInfo:
        """
        Retrieves the server information.

        :return: A ServerInfo object containing server information
        :raises ServerNotFoundException: If no TCP connection can be established
        :raises InvalidPacketException: If the server does not answer like a TrackMania server
        """
        request_id = secrets.randbelow(0x7FFFFFFF) + 1

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=self._timeout
            )
        except (OSError, asyncio.TimeoutError) as e:
            raise ServerNotFoundException(
                f"Failed to connect to {self._host}:{self._port}: {e}"
            ) from e

        try:
            writer.write(
                self.build_connection_admin(self._SUBTYPE_QUERY_MODE)
                + self.build_connection_admin(self._SUBTYPE_INFO_REQUEST, request_id)
            )
            await writer.drain()

            data = await asyncio.wait_for(
                self._receive_info(reader, request_id), timeout=self._timeout
            )
        except asyncio.TimeoutError as e:
            raise InvalidPacketException("Timeout while waiting for server info") from e
        except asyncio.IncompleteReadError as e:
            raise InvalidPacketException("Connection closed by the server") from e
        except OSError as e:
            raise InvalidPacketException(f"Connection error: {e}") from e
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

        return self.parse_server_info(data)

    async def _receive_info(
        self, reader: asyncio.StreamReader, request_id: int
    ) -> bytes:
        while True:
            length = struct.unpack("<I", await reader.readexactly(4))[0]

            if not 2 <= length <= self._MAX_MESSAGE_SIZE:
                raise InvalidPacketException(f"Invalid message length: {length}")

            message_type, payload = self.decode_message(
                await reader.readexactly(length)
            )

            if message_type != self._MESSAGE_CONNECTION_ADMIN:
                continue

            data = self._read_info_reply(payload, request_id)

            if data is not None:
                return data

    def _read_info_reply(self, payload: bytes, request_id: int) -> bytes | None:
        reader = _Reader(payload)
        version = reader.u32()
        subtype = reader.u32()

        if version != self._CONNECTION_ADMIN_VERSION:
            raise InvalidPacketException(
                f"Unsupported ConnectionAdmin version: {version}"
            )

        if subtype == self._SUBTYPE_REFUSED:
            raise InvalidPacketException("The server refused the query")

        if subtype != self._SUBTYPE_INFO:
            return None

        reply_id = reader.u32()
        data = reader.take(reader.u32())

        if reply_id == self._NO_INFO:
            raise InvalidPacketException("The server has no game info available yet")

        return data if reply_id == request_id else None

    @classmethod
    def build_connection_admin(
        cls, subtype: int, request_id: int | None = None
    ) -> bytes:
        """Builds a framed CNetFormConnectionAdmin message."""
        payload = struct.pack("<II", cls._CONNECTION_ADMIN_VERSION, subtype)

        if request_id is not None:
            payload += struct.pack("<I", request_id)

        return cls.build_message(cls._MESSAGE_CONNECTION_ADMIN, payload)

    @classmethod
    def build_message(cls, message_type: int, payload: bytes) -> bytes:
        """Builds a framed, checksummed and uncompressed message."""
        message = bytearray([0x80 | cls._FLAG_CHECKSUM, message_type])
        message += bytes(4) + payload
        message[2:6] = struct.pack("<I", cls._checksum(message, 2))

        return struct.pack("<I", len(message)) + bytes(message)

    @classmethod
    def decode_message(cls, message: bytes) -> tuple[int, bytes]:
        """
        Decodes a message without its length prefix.

        :return: Message type and (decompressed) payload
        """
        if len(message) < 2 or message[0] & 0xF0 != 0x80:
            raise InvalidPacketException("Invalid message header")

        flags, message_type = message[0], message[1]
        position = 2

        if flags & cls._FLAG_SEQUENCE:
            position += 2

        if flags & cls._FLAG_CHECKSUM:
            if len(message) < position + 4:
                raise InvalidPacketException("Truncated message")

            checksum = struct.unpack_from("<I", message, position)[0]

            if checksum != cls._checksum(message, position):
                raise InvalidPacketException("Message checksum mismatch")

            position += 4

        if not flags & cls._FLAG_COMPRESSED:
            return message_type, bytes(message[position:])

        if len(message) < position + 4:
            raise InvalidPacketException("Truncated message")

        size = struct.unpack_from("<I", message, position)[0]

        if size > cls._MAX_MESSAGE_SIZE:
            raise InvalidPacketException(f"Invalid uncompressed size: {size}")

        return message_type, _lzo1x_decompress(message[position + 4 :], size)

    @classmethod
    def _checksum(cls, message: bytes, position: int) -> int:
        data = bytearray(message)
        data[position : position + 4] = bytes(4)
        digest = hmac.new(cls._CHECKSUM_KEY, bytes(data), hashlib.md5).digest()

        return sum(struct.unpack("<4I", digest)) & 0xFFFFFFFF

    @classmethod
    def parse_server_info(cls, data: bytes) -> ServerInfo:
        """
        Parses the server info sent in reply to an info request.

        Layout, one block per class of the serialisation chain::

            CNetMasterHost
                u8      game tag: (tag & 0xE0) == 0x20, (tag & 0x1F) == 0x0D
                u8[4]   IP address, reversed byte order
                u16     port
                str     host login
            CGameNetServerInfo
                str     "#SRV#" + "p" player password / "s" spectator password / "f" both
            CGameCtnNetServerInfo                  (only for a "#SRV#" login)
                str     unused, always empty
                u8      player count, max players, spectator count, max spectators,
                        ladder mode
                wstr    server name
                str     pack mask
                u32 n   wstr player names[n], i32 ladder rankings[n]
                wstr    comment
            CTrackManiaNetworkServerInfo
                u8      game mode (GAME_MODES)
                u32     time limit (ms) / points limit / number of laps
                u8      number of challenges in the playlist
                u32 n   challenges[n]: wstr name, u32 gold time, u16 copper price,
                        u8 environment index; current challenge first
                u32 n   environment ids[n] (Nadeo lookback strings)
        """
        reader = _Reader(data)
        game_tag = reader.u8()

        if game_tag & 0xE0 != 0x20 or game_tag & 0x1F != cls._GAME_TAG_TRACKMANIA:
            raise InvalidPacketException(
                f"Not a TrackMania server (game tag 0x{game_tag:02x})"
            )

        address = ".".join(str(octet) for octet in reversed(reader.take(4)))
        port = reader.u16()
        server_login = reader.string()
        player_login = reader.string()

        info = ServerInfo(
            name=server_login,
            map="",
            players=0,
            max_players=0,
            game_mode="Unknown",
            server_login=server_login,
            pc_guid=server_login,
            server_address=address,
            server_port=port,
            local_ip=address,
            raw_data=data.hex(),
        )

        if not player_login.startswith("#SRV#"):
            return info

        password_flag = player_login[5:6]
        info.password_protected = info.private_server = password_flag in ("p", "f")
        info.spectator_password_protected = password_flag in ("s", "f")

        reader.string()
        info.players = reader.u8()
        info.max_players = reader.u8()
        info.spectators = reader.u8()
        info.max_spectators = info.spectator_slots = reader.u8()
        info.ladder_mode = reader.u8()
        info.ladder_server = info.ladder_mode != 0
        info.name = reader.wstring()
        info.pack_mask = reader.string()

        names = [reader.wstring() for _ in range(reader.count())]
        info.player_list = [Player(name, reader.i32()) for name in names]
        info.comment = reader.wstring()

        if reader.remaining == 0:
            return info

        info.game_mode_id = reader.u8()
        info.game_mode = cls.GAME_MODES.get(
            info.game_mode_id, f"Unknown ({info.game_mode_id})"
        )
        limit = reader.u32()

        if info.game_mode_id in (1, 8):
            info.time_limit = limit
        elif info.game_mode_id == 7:
            info.nb_laps = limit
        elif info.game_mode_id in (3, 6, 9):
            info.points_limit = limit

        info.nb_challenges = reader.u8()
        challenges = [
            (reader.wstring(), reader.u32(), reader.u16(), reader.u8())
            for _ in range(reader.count())
        ]
        ids = _IdReader(reader)
        environments = [ids.read() for _ in range(reader.count())]

        info.challenges = [
            Challenge(
                name,
                gold_time,
                copper_price,
                environments[index] if index < len(environments) else "Unknown",
            )
            for name, gold_time, copper_price, index in challenges
        ]

        if info.challenges:
            info.map = info.challenges[0].name
            info.environment = info.challenges[0].environment
        elif info.pack_mask:
            info.environment = info.pack_mask

        return info


class _Reader:
    """Bounds-checked little-endian reader for Nadeo archives."""

    def __init__(self, data: bytes):
        self._data = data
        self._position = 0

    @property
    def remaining(self) -> int:
        return len(self._data) - self._position

    def take(self, count: int) -> bytes:
        if count < 0 or count > self.remaining:
            raise InvalidPacketException("Truncated server info")

        data = self._data[self._position : self._position + count]
        self._position += count

        return data

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return struct.unpack("<H", self.take(2))[0]

    def u32(self) -> int:
        return struct.unpack("<I", self.take(4))[0]

    def i32(self) -> int:
        return struct.unpack("<i", self.take(4))[0]

    def count(self) -> int:
        # Every list element takes at least one byte.
        count = self.u32()

        if count > self.remaining:
            raise InvalidPacketException(f"Invalid list length: {count}")

        return count

    def string(self) -> str:
        return self.take(self.u32()).decode("utf-8", errors="replace")

    def wstring(self) -> str:
        return self.take(self.u32()).decode("utf-8-sig", errors="replace")


class _IdReader:
    """Reads Nadeo identifiers ("lookback strings") sharing one string table."""

    def __init__(self, reader: _Reader):
        self._reader = reader
        self._version: int | None = None
        self._strings: list[str] = []

    def read(self) -> str:
        if self._version is None:
            self._version = self._reader.u32()

            if self._version not in (2, 3):
                raise InvalidPacketException(f"Unsupported id version: {self._version}")

        value = self._reader.u32()

        if value == 0xFFFFFFFF:
            return ""

        if value & 0xC0000000 not in (0x40000000, 0x80000000):
            # Numeric collection id
            return str(value)

        index = value & 0x0FFFFFFF

        if self._version == 2 or index == 0:
            string = self._reader.string()
            self._strings.append(string)
            return string

        if index > len(self._strings):
            raise InvalidPacketException(f"Invalid id reference: {index}")

        return self._strings[index - 1]


def _lzo1x_decompress(source: bytes, size: int) -> bytes:
    """Decompresses an LZO1X stream into exactly size bytes."""
    output = bytearray()
    position = 0

    def copy_literals(count: int):
        nonlocal position

        if position + count > len(source) or len(output) + count > size:
            raise InvalidPacketException("Corrupted LZO stream")

        output.extend(source[position : position + count])
        position += count

    def copy_match(distance_position: int, count: int):
        if distance_position < 0 or len(output) + count > size:
            raise InvalidPacketException("Corrupted LZO stream")

        for i in range(count):
            output.append(output[distance_position + i])

    def read_length(base: int) -> int:
        nonlocal position
        length = 0

        while source[position] == 0:
            length += 255
            position += 1

        length += base + source[position]
        position += 1

        return length

    try:
        # 0: next code < 16 is a literal run, 1-3: a 2 byte match follows
        # the trailing literals, 4: a 3 byte match follows a literal run.
        state = 0

        if source[0] > 17:
            position = 1
            count = source[0] - 17
            copy_literals(count)
            state = min(4, count)

        while True:
            code = source[position]
            position += 1

            if code < 16:
                if state == 0:
                    copy_literals((code or read_length(15)) + 3)
                    state = 4
                    continue

                distance = (code >> 2) + (source[position] << 2)
                position += 1

                if state == 4:
                    copy_match(len(output) - 0x801 - distance, 3)
                else:
                    copy_match(len(output) - 1 - distance, 2)
            elif code >= 64:
                distance = ((code >> 2) & 7) + (source[position] << 3)
                position += 1
                copy_match(len(output) - 1 - distance, (code >> 5) + 1)
            elif code >= 32:
                count = (code & 31 or read_length(31)) + 2
                distance = (source[position] | source[position + 1] << 8) >> 2
                position += 2
                copy_match(len(output) - 1 - distance, count)
            else:
                count = (code & 7 or read_length(7)) + 2
                distance = ((code & 8) << 11) + (
                    (source[position] | source[position + 1] << 8) >> 2
                )
                position += 2

                if distance == 0:
                    break

                copy_match(len(output) - distance - 0x4000, count)

            state = source[position - 2] & 3

            if state:
                copy_literals(state)
    except IndexError as e:
        raise InvalidPacketException("Truncated LZO stream") from e

    if len(output) != size:
        raise InvalidPacketException("LZO size mismatch")

    return bytes(output)
