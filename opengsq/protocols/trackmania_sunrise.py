"""
TrackMania Original/Sunrise/Nations ESWC native server query.

The three games share one dedicated server, TrackManiaServer.exe, started with
/game=Original, /game=Sunrise or /game=Nations, and one network protocol: the
predecessor of the TmForever protocol (see trackmania_nations.py).
Reverse-engineered from TrackManiaServer.exe of TrackMania Sunrise eXtreme.

All integers are little-endian. Framing, message header and LZO1X compression
are the same as for TmForever::

    u32 length (TCP only) | u8 flags | u8 type | [u16 sequence] | [u32 checksum] | payload

The checksum uses another key and adds the first key word instead of the
fourth digest word::

    w = HMAC-MD5(_CHECKSUM_KEY, message with the checksum zeroed) as four u32
    checksum = w[0] + w[1] + w[2] + key[0]

The server does not require it for the messages used here, but it sets it on
every reply, which the query uses to recognise a TrackMania server.

TCP query on the game port (default 2350), CNetFormConnectionAdmin (type 3)::

    u32 version   4 (Original, Sunrise) or 5 (Nations ESWC). A lower version
                  is refused with subtype 1 (the reply carries the server
                  version), a higher one is ignored.
    u32 subtype   8: switch the connection into query mode (no payload)
                  7: u32 request_id                         (client -> server)
                  6: u32 request_id | u32 size | u8[size]   (server -> client)

UDP LAN discovery on the game port, a server only answers for its own game id::

    CNetFormQuerrySessions (type 0): str game_id | str client | addr | u32 nonce
    CNetFormEnumSessions   (type 1): u32 nonce | str application | str game_id
                                     | str version | str host_name | addr | addr

addr is the IPv4 address in reversed byte order followed by the u16 port.
str is u32 length + bytes, wstr the same with UTF-8 (prefixed by a BOM if it
contains non-ASCII characters).
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import struct
from typing import Optional, Tuple

from opengsq.exceptions import InvalidPacketException, ServerNotFoundException
from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.protocols.trackmania_nations import _lzo1x_decompress, _Reader
from opengsq.responses.trackmania_sunrise import (
    Challenge,
    Player,
    ServerInfo,
    SessionInfo,
)


class TrackmaniaSunrise(ProtocolBase):
    """
    TrackMania Original/Sunrise/Nations ESWC Protocol Implementation
    """

    @property
    def full_name(self) -> str:
        return "TrackMania Sunrise Protocol"

    DEFAULT_PORT = 2350

    # Game ids the server compares LAN session queries against
    GAMES = {
        "TmOriginal": "TrackMania Original",
        "TmSunrise": "TrackMania Sunrise",
        "TmNationsESWC": "TrackMania Nations ESWC",
    }

    GAME_MODES = {
        1: "TimeAttack",
        3: "Rounds",
        6: "Team",
        7: "Laps",
        8: "Stunts",
    }

    _FLAG_COMPRESSED = 0x01
    _FLAG_CHECKSUM = 0x02
    _FLAG_SEQUENCE = 0x0C

    _MESSAGE_QUERY_SESSIONS = 0x00
    _MESSAGE_ENUM_SESSIONS = 0x01
    _MESSAGE_CONNECTION_ADMIN = 0x03

    # ConnectionAdmin version of Original/Sunrise and of Nations ESWC
    _VERSION_SUNRISE = 4
    _VERSION_NATIONS_ESWC = 5

    _SUBTYPE_REFUSED = 1
    _SUBTYPE_INFO = 6
    _SUBTYPE_INFO_REQUEST = 7
    _SUBTYPE_QUERY_MODE = 8

    # Request id the server puts into the reply when it has no game info yet.
    _NO_INFO = 0xFFFFFFFF

    _CHECKSUM_KEY = bytes.fromhex("08c481303a1226abaf1d6ae4fb65fbc9")
    _MAX_MESSAGE_SIZE = 0x100000

    # First byte of the server info: high bits 000 = valid, low bits = game.
    # The game id is known for Nations ESWC only, Original and Sunrise share 0x07.
    _GAME_TAGS = {0x07: "", 0x09: "TmNationsESWC"}

    _CLIENT_NAME = "opengsq"

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 5.0):
        super().__init__(host, port, timeout)

    async def get_info(self) -> ServerInfo:
        """
        Retrieves the server information via TCP.

        Original and Sunrise servers cannot be told apart by this query
        (game_id is empty for them), use get_session() for that.

        :return: A ServerInfo object containing server information
        :raises ServerNotFoundException: If no TCP connection can be established
        :raises InvalidPacketException: If the server does not answer like a TrackMania server
        """
        version = self._VERSION_SUNRISE

        try:
            data = await self._query_info(version)
        except _RefusedException as e:
            # Nations ESWC refuses the Original/Sunrise version and tells its own
            if e.server_version != self._VERSION_NATIONS_ESWC:
                raise InvalidPacketException(
                    f"The server refused the query (version {e.server_version})"
                ) from e

            version = e.server_version
            data = await self._query_info(version)

        info = self.parse_server_info(data)
        info.protocol_version = version

        return info

    async def get_session(self, game_id: Optional[str] = None) -> SessionInfo:
        """
        Retrieves the LAN session announcement of the server via UDP.

        The server only answers for its own game, so this identifies whether
        it runs TrackMania Original, Sunrise or Nations ESWC.

        :param game_id: Game id to ask for (TmOriginal, TmSunrise or TmNationsESWC),
            all of them if omitted
        :return: A SessionInfo object
        :raises ServerNotFoundException: If no matching server answers
        """
        game_ids = [game_id] if game_id else list(self.GAMES)
        nonce = secrets.randbits(32)

        with UdpClient() as udp_client:
            udp_client.settimeout(self._timeout)
            await udp_client.connect((self._host, self._port))

            for query_game_id in game_ids:
                udp_client.send(self.build_session_query(query_game_id, nonce))

            try:
                return await asyncio.wait_for(
                    self._receive_session(udp_client, nonce), timeout=self._timeout
                )
            except asyncio.TimeoutError as e:
                raise ServerNotFoundException(
                    f"No TrackMania session announced by {self._host}:{self._port}"
                ) from e

    async def _receive_session(self, udp_client: UdpClient, nonce: int) -> SessionInfo:
        while True:
            try:
                return self.parse_session_reply(await udp_client.recv(), nonce)
            except InvalidPacketException:
                continue

    async def _query_info(self, version: int) -> bytes:
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
                self.build_connection_admin(self._SUBTYPE_QUERY_MODE, version=version)
                + self.build_connection_admin(
                    self._SUBTYPE_INFO_REQUEST, request_id, version=version
                )
            )
            await writer.drain()

            return await asyncio.wait_for(
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

    def _read_info_reply(self, payload: bytes, request_id: int) -> Optional[bytes]:
        reader = _Reader(payload)
        version = reader.u32()
        subtype = reader.u32()

        if subtype == self._SUBTYPE_REFUSED:
            raise _RefusedException(version)

        if version not in (self._VERSION_SUNRISE, self._VERSION_NATIONS_ESWC):
            raise InvalidPacketException(
                f"Unsupported ConnectionAdmin version: {version}"
            )

        if subtype != self._SUBTYPE_INFO:
            return None

        reply_id = reader.u32()
        data = reader.take(reader.u32())

        if reply_id == self._NO_INFO:
            raise InvalidPacketException("The server has no game info available yet")

        return data if reply_id == request_id else None

    @classmethod
    def build_connection_admin(
        cls,
        subtype: int,
        request_id: Optional[int] = None,
        version: int = _VERSION_SUNRISE,
    ) -> bytes:
        """Builds a framed CNetFormConnectionAdmin message."""
        payload = struct.pack("<II", version, subtype)

        if request_id is not None:
            payload += struct.pack("<I", request_id)

        message = cls.build_message(cls._MESSAGE_CONNECTION_ADMIN, payload)

        return struct.pack("<I", len(message)) + message

    @classmethod
    def build_session_query(
        cls, game_id: str, nonce: int, client_name: str = _CLIENT_NAME
    ) -> bytes:
        """Builds a CNetFormQuerrySessions datagram for LAN discovery."""
        payload = (
            _pack_string(game_id)
            + _pack_string(client_name)
            + bytes(6)  # Address, not used by the server
            + struct.pack("<I", nonce)
        )

        return cls.build_message(cls._MESSAGE_QUERY_SESSIONS, payload)

    @classmethod
    def build_message(cls, message_type: int, payload: bytes) -> bytes:
        """Builds a checksummed and uncompressed message without length prefix."""
        message = bytearray([0x80 | cls._FLAG_CHECKSUM, message_type])
        message += bytes(4) + payload
        message[2:6] = struct.pack("<I", cls._checksum(message, 2))

        return bytes(message)

    @classmethod
    def decode_message(cls, message: bytes) -> Tuple[int, bytes]:
        """
        Decodes a message without its length prefix.

        The checksum is mandatory: every message of a TrackMania server carries one.

        :return: Message type and (decompressed) payload
        """
        if len(message) < 2 or message[0] & 0xF0 != 0x80:
            raise InvalidPacketException("Invalid message header")

        flags, message_type = message[0], message[1]
        position = 2

        if flags & cls._FLAG_SEQUENCE:
            position += 2

        if not flags & cls._FLAG_CHECKSUM:
            raise InvalidPacketException("Message without checksum")

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
        words = struct.unpack("<4I", digest)
        key = struct.unpack_from("<I", cls._CHECKSUM_KEY)[0]

        return (words[0] + words[1] + words[2] + key) & 0xFFFFFFFF

    @classmethod
    def parse_session_reply(
        cls, datagram: bytes, nonce: Optional[int] = None
    ) -> SessionInfo:
        """
        Parses a CNetFormEnumSessions datagram sent in reply to a session query.

        :param nonce: Nonce of the query, the reply must echo it if given
        :raises InvalidPacketException: If the datagram is no matching reply
        """
        message_type, payload = cls.decode_message(datagram)

        if message_type != cls._MESSAGE_ENUM_SESSIONS:
            raise InvalidPacketException(f"Unexpected message type: {message_type}")

        reader = _Reader(payload)
        reply_nonce = reader.u32()

        if nonce is not None and reply_nonce != nonce:
            raise InvalidPacketException("Reply to another session query")

        application = reader.string()
        game_id = reader.string()
        version = reader.string()
        host_name = reader.string()
        address, port = _read_address(reader)
        secondary_address, secondary_port = _read_address(reader)

        return SessionInfo(
            game_id=game_id,
            game=cls.GAMES.get(game_id, game_id),
            version=version,
            host_name=host_name,
            application=application,
            server_address=address,
            server_port=port,
            secondary_address=secondary_address,
            secondary_port=secondary_port,
        )

    @classmethod
    def parse_server_info(cls, data: bytes) -> ServerInfo:
        """
        Parses the server info sent in reply to an info request.

        Layout, one block per class of the serialisation chain::

            CNetMasterHost
                u8      game tag: (tag & 0xE0) == 0, (tag & 0x1F) == 0x07 or 0x09
                u8[4]   IP address, reversed byte order
                u16     port
                str     host login
            CGameNetServerInfo
                str     "#SRV#" + "p" player password / "s" spectator password / "f" both
            game server info                       (only for a "#SRV#" login)
                wstr    unused, always empty
                u8      player count, max players, spectator count, max spectators,
                        ladder mode
                wstr    server name
                u32 n   wstr player names[n], i32 ladder rankings[n]
                wstr    comment
            CTrackManiaNetworkServerInfo
                u8      game mode (GAME_MODES)
                u32     time limit (ms) / points limit / number of laps
                u8      number of challenges in the playlist
                u32 n   challenges[n]: wstr name, u32 decoration index,
                        u32 gold time, u32 copper price; current challenge first
        """
        reader = _Reader(data)
        game_tag = reader.u8()

        if game_tag & 0xE0 != 0 or game_tag not in cls._GAME_TAGS:
            raise InvalidPacketException(
                f"Not a TrackMania Sunrise server (game tag 0x{game_tag:02x})"
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
            game_id=cls._GAME_TAGS[game_tag],
            game_tag=game_tag,
            server_login=server_login,
            server_address=address,
            server_port=port,
            raw_data=data.hex(),
        )

        if not player_login.startswith("#SRV#"):
            return info

        password_flag = player_login[5:6]
        info.password_protected = password_flag in ("p", "f")
        info.spectator_password_protected = password_flag in ("s", "f")

        reader.wstring()
        info.players = reader.u8()
        info.max_players = reader.u8()
        info.spectators = reader.u8()
        info.max_spectators = reader.u8()
        info.ladder_mode = reader.u8()
        info.ladder_server = info.ladder_mode != 0
        info.name = reader.wstring()

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
        elif info.game_mode_id in (3, 6):
            info.points_limit = limit

        info.nb_challenges = reader.u8()
        info.challenges = [
            Challenge(
                name=reader.wstring(),
                decoration_index=reader.u32(),
                gold_time=reader.u32(),
                copper_price=reader.u32(),
            )
            for _ in range(reader.count())
        ]

        if info.challenges:
            info.map = info.challenges[0].name

        return info


class _RefusedException(InvalidPacketException):
    """The server refused the ConnectionAdmin version (subtype 1)."""

    def __init__(self, server_version: int):
        super().__init__(f"The server refused the query (version {server_version})")
        self.server_version = server_version


def _pack_string(text: str) -> bytes:
    data = text.encode("utf-8")
    return struct.pack("<I", len(data)) + data


def _read_address(reader: _Reader) -> Tuple[str, int]:
    address = ".".join(str(octet) for octet in reversed(reader.take(4)))
    return address, reader.u16()


if __name__ == "__main__":
    import json
    import sys

    async def main_async():
        host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
        tm = TrackmaniaSunrise(host, TrackmaniaSunrise.DEFAULT_PORT, 5.0)
        info = await tm.get_info()
        print(json.dumps(info.to_dict(), indent=4, ensure_ascii=False))
        session = await tm.get_session()
        print(json.dumps(session.to_dict(), indent=4, ensure_ascii=False))

    asyncio.run(main_async())
