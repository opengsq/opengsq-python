import asyncio
import struct

import pytest

from opengsq.exceptions import InvalidPacketException, ServerNotFoundException
from opengsq.protocols.trackmania_sunrise import TrackmaniaSunrise

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

# Test server configuration (TrackMania Sunrise eXtreme dedicated server)
SERVER_IP = "10.10.101.4"
SERVER_PORT = 2350

tms = TrackmaniaSunrise(host=SERVER_IP, port=SERVER_PORT)

# Requests the live server answered (version 4, request id 0x1234)
CLIENT_QUERY_MODE = bytes.fromhex("0e00000082038b9433740400000008000000")
CLIENT_INFO_REQUEST = bytes.fromhex("12000000820346e5b853040000000700000034120000")

# Reply of a TrackMania Sunrise eXtreme dedicated server to request id 0x1234
SERVER_INFO_REPLY = bytes.fromhex(
    "330200008303adf73b18770200000006040000000600000034120000670200000704650a0a2e09"
    "0f480200074445534b544f502d4a424b4c354a3005000000235352562300600002200020001244"
    "020f53756e72697365204c414e2053657276657275031e580708547261636b4d616e696120f004"
    "0345787472656d90050401e093040036144408080b0000004e69676874466c75000d580106ee98"
    "0000ab050000075803054361725061726b0c580203f6900000d104b80204585261636530346404"
    "0005e83401009d0700000a00000041717561536368656d65095c1005c07f01009f0500006c0106"
    "4772616e64507269786806053c9b0000720500006c1a03536e616b6508540503d87c00004f06bc"
    "08074368616f73204172656168040678690000d50200000e54040b506172616469736549736c61"
    "6e647c240274d10000f42b590237681105e4b001004907000064170954756e6e656c4566666563"
    "74600a02fc20010022c80d07536d616c6c2052696e67640505384a0000c2030000782005416572"
    "69616c204c792273600202a8610000635c07741506446f776e746f776e03402303cecc00004906"
    "bc1c075370656564576176650e501502e0a50100b1c0290456696c6c616765781f0286c9000026"
    "543e7c0806486170707942617902580502e86e0300a42b250332540d0400e0b00000c707b80b05"
    "4d61676e697475649c2b0c1e1d0100900500000b000000557020412c207812741f03307500005b"
    "032aac060a3502000000722d0100b8070000110000"
)

# Session query for TmSunrise (nonce 0xC0FFEE, client name "x") and the reply
CLIENT_SESSION_QUERY = bytes.fromhex(
    "8200358ea5ef09000000546d53756e726973650100000078000000000000eeffc000"
)
SERVER_SESSION_REPLY = bytes.fromhex(
    "820186ed3e6eeeffc0000700000047616d654e657409000000546d53756e726973650500000031"
    "2e3034330f0000004445534b544f502d4a424b4c354a3004650a0a2e0904650a0a2e09"
)

# Reply of a TmForever server, which uses another checksum key
TMNF_INFO_REPLY = bytes.fromhex(
    "9b0000008303681ac2009b0000000a0700000006000000d53d41008b5c00000b2d1d641dac2e09"
    "0900000050432d636539623063050000002353525623500204000106000600094402074b617761"
    "626f6e6761075001075374616469756d0100002c6c0001ffffffff940602e09304000178030001"
    "080000004230322d526163657a710000b9020079020374040b000040070000005374616469756d"
    "110000"
)


def _decode_captured_info() -> bytes:
    message_type, payload = TrackmaniaSunrise.decode_message(SERVER_INFO_REPLY[4:])
    assert message_type == 3

    return tms._read_info_reply(payload, 0x1234)


def _server_info(
    name: str = "Sunrise LAN Server",
    login: str = "#SRV#",
    game_tag: int = 0x07,
    players=(),
) -> bytes:
    """Builds a server info payload like the server serialises it."""

    def wstr(text: str) -> bytes:
        data = text.encode("utf-8")
        if text != text.encode("ascii", "ignore").decode():
            data = b"\xef\xbb\xbf" + data
        return struct.pack("<I", len(data)) + data

    data = bytes([game_tag]) + bytes([4, 101, 10, 10]) + struct.pack("<H", 2350)
    data += wstr("HOST") + wstr(login) + wstr("")
    data += bytes([len(players), 16, 0, 8, 0]) + wstr(name)
    data += struct.pack("<I", len(players))
    data += b"".join(wstr(player) for player in players)
    data += b"".join(struct.pack("<i", -1) for _ in players)
    data += wstr("Kommentar")
    data += bytes([3]) + struct.pack("<I", 30) + bytes([1]) + struct.pack("<I", 1)
    data += wstr("A01-Race") + struct.pack("<III", 2, 25000, 600)

    return data


@pytest.mark.asyncio
async def test_get_info():
    session = await tms.get_session()
    result = await tms.get_info(session.game_id)
    await handler.save_result("test_get_info", result)


@pytest.mark.asyncio
async def test_get_session():
    result = await tms.get_session()
    await handler.save_result("test_get_session", result)


def test_build_requests_match_live_server():
    assert TrackmaniaSunrise.build_connection_admin(8) == CLIENT_QUERY_MODE
    assert TrackmaniaSunrise.build_connection_admin(7, 0x1234) == CLIENT_INFO_REQUEST
    assert (
        TrackmaniaSunrise.build_session_query("TmSunrise", 0xC0FFEE, "x")
        == CLIENT_SESSION_QUERY
    )


def test_parse_captured_server_info():
    info = TrackmaniaSunrise.parse_server_info(_decode_captured_info())

    assert info.name == "Sunrise LAN Server"
    assert info.comment == "TrackMania Sunrise Extreme LAN"
    assert (info.game_tag, info.game_id) == (0x07, "")
    assert info.server_login == "DESKTOP-JBKL5J0"
    assert (info.server_address, info.server_port) == ("10.10.101.4", 2350)
    assert (info.players, info.max_players) == (0, 32)
    assert (info.spectators, info.max_spectators) == (0, 32)
    assert info.password_protected is False
    assert info.spectator_password_protected is False
    assert info.ladder_mode == 0
    assert info.player_list == []
    assert (info.game_mode, info.game_mode_id, info.time_limit) == (
        "TimeAttack",
        1,
        300000,
    )
    assert info.nb_challenges == 54
    assert len(info.challenges) == 20
    assert info.map == "NightFlight"
    assert info.challenges[0].gold_time == 39150
    assert info.challenges[0].copper_price == 1451
    assert info.challenges[0].decoration_index == 13
    assert info.challenges[15].name == "HappyBay"
    assert info.challenges[-1].name == "XRace05"
    # Original and Sunrise share the game tag, the environment needs the game id
    assert (info.environment, info.challenges[0].environment) == ("", "")


def test_parse_captured_server_info_with_game_id():
    info = TrackmaniaSunrise.parse_server_info(_decode_captured_info(), "TmSunrise")
    challenges = {challenge.name: challenge for challenge in info.challenges}

    assert info.game_id == "TmSunrise"
    assert (info.map, info.environment, info.mood) == ("NightFlight", "Island", "Night")
    assert (challenges["HappyBay"].environment, challenges["HappyBay"].mood) == (
        "Bay",
        "Day",
    )
    assert (challenges["Downtown"].environment, challenges["Downtown"].mood) == (
        "Bay",
        "Night",
    )
    assert (
        challenges["ParadiseIsland"].environment,
        challenges["ParadiseIsland"].mood,
    ) == ("Island", "Sunset")


@pytest.mark.parametrize(
    "game_id, decoration_index, expected",
    [
        ("TmSunrise", 2, ("Bay", "Day")),
        ("TmSunrise", 3, ("Bay", "Night")),
        ("TmSunrise", 4, ("Bay", "Sunrise")),
        ("TmSunrise", 5, ("Bay", "Sunset")),
        ("TmSunrise", 6, ("Bay", "")),
        ("TmSunrise", 7, ("Coast", "Day")),
        ("TmSunrise", 13, ("Island", "Night")),
        ("TmSunrise", 16, ("Island", "")),
        ("TmSunrise", 17, None),
        ("TmSunrise", 0, None),
        ("TmOriginal", 2, ("Alpine", "10x150")),
        ("TmOriginal", 3, ("Alpine", "10x150Sunrise")),
        ("TmOriginal", 13, ("Alpine", "Simple")),
        ("TmOriginal", 14, ("Alpine", "")),
        ("TmOriginal", 15, ("Rally", "10x150")),
        ("TmOriginal", 40, ("Speed", "")),
        ("TmOriginal", 41, None),
        ("TmNationsESWC", 2, ("Stadium", "Day")),
        ("TmNationsESWC", 3, ("Stadium", "")),
        ("", 2, None),
    ],
)
def test_decoration(game_id, decoration_index, expected):
    assert TrackmaniaSunrise.decoration(game_id, decoration_index) == expected


def test_game_id_from_game_tag_wins():
    eswc = TrackmaniaSunrise.parse_server_info(_server_info(game_tag=0x09), "TmSunrise")
    sunrise = TrackmaniaSunrise.parse_server_info(_server_info(), "TmNationsESWC")

    assert (eswc.game_id, eswc.environment) == ("TmNationsESWC", "Stadium")
    assert (sunrise.game_id, sunrise.environment) == ("", "")


def test_parse_session_reply():
    session = TrackmaniaSunrise.parse_session_reply(SERVER_SESSION_REPLY, 0xC0FFEE)

    assert (session.game_id, session.game) == ("TmSunrise", "TrackMania Sunrise")
    assert session.version == "1.043"
    assert session.application == "GameNet"
    assert session.host_name == "DESKTOP-JBKL5J0"
    assert (session.server_address, session.server_port) == ("10.10.101.4", 2350)
    assert (session.secondary_address, session.secondary_port) == ("10.10.101.4", 2350)


def test_rejects_session_reply_with_other_nonce():
    with pytest.raises(InvalidPacketException):
        TrackmaniaSunrise.parse_session_reply(SERVER_SESSION_REPLY, 0x1234)


def test_parse_built_server_info():
    info = TrackmaniaSunrise.parse_server_info(
        _server_info(name="$o$f00Grüne $fffWelle", players=["$f00Gamie", "Spieler 2"])
    )

    assert info.name == "$o$f00Grüne $fffWelle"
    assert info.plain_name == "Grüne Welle"
    assert (info.players, info.max_players) == (2, 16)
    assert (info.spectators, info.max_spectators) == (0, 8)
    assert [(p.name, p.ladder_ranking) for p in info.player_list] == [
        ("$f00Gamie", -1),
        ("Spieler 2", -1),
    ]
    assert (info.game_mode, info.points_limit, info.time_limit) == ("Rounds", 30, 0)
    assert info.map == "A01-Race"


@pytest.mark.parametrize(
    "login, player_password, spectator_password",
    [
        ("#SRV#", False, False),
        ("#SRV#p", True, False),
        ("#SRV#s", False, True),
        ("#SRV#f", True, True),
    ],
)
def test_password_flags_from_server_login(login, player_password, spectator_password):
    info = TrackmaniaSunrise.parse_server_info(_server_info(login=login))

    assert info.password_protected is player_password
    assert info.spectator_password_protected is spectator_password


def test_nations_eswc_game_tag():
    info = TrackmaniaSunrise.parse_server_info(_server_info(game_tag=0x09))

    assert (info.game_tag, info.game_id) == (0x09, "TmNationsESWC")
    assert (info.environment, info.mood) == ("Stadium", "Day")


@pytest.mark.parametrize("game_tag", [0x2D, 0x0D, 0x27, 0x08])
def test_rejects_other_game_tag(game_tag):
    with pytest.raises(InvalidPacketException):
        TrackmaniaSunrise.parse_server_info(_server_info(game_tag=game_tag))


def test_rejects_tmforever_reply():
    with pytest.raises(InvalidPacketException):
        TrackmaniaSunrise.decode_message(TMNF_INFO_REPLY[4:])


def test_rejects_corrupted_checksum():
    corrupted = bytearray(SERVER_INFO_REPLY[4:])
    corrupted[-1] ^= 0xFF

    with pytest.raises(InvalidPacketException):
        TrackmaniaSunrise.decode_message(bytes(corrupted))


def test_rejects_message_without_checksum():
    with pytest.raises(InvalidPacketException):
        TrackmaniaSunrise.decode_message(b"\x80\x03" + struct.pack("<II", 4, 8))


def test_rejects_truncated_server_info():
    with pytest.raises(InvalidPacketException):
        TrackmaniaSunrise.parse_server_info(_decode_captured_info()[:60])


async def _serve_info(versions: dict, received: list):
    """
    Starts a fake server. versions maps the ConnectionAdmin version of a request
    to the server info to answer with, other versions are refused with the last
    version of the mapping.
    """
    server_version = list(versions)[-1]

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        for _ in range(2):
            length = struct.unpack("<I", await reader.readexactly(4))[0]
            message_type, payload = TrackmaniaSunrise.decode_message(
                await reader.readexactly(length)
            )
            received.append((message_type, payload))

        version, _, request_id = struct.unpack_from("<III", received[-1][1])

        if version not in versions:
            reply = struct.pack("<III", server_version, 1, 0)
        else:
            info_data = versions[version]
            reply = struct.pack("<IIII", version, 6, request_id, len(info_data))
            reply += info_data

        message = TrackmaniaSunrise.build_message(0x03, reply)

        # An unrelated message and a stale reply must be skipped
        if version in versions:
            other = TrackmaniaSunrise.build_message(0x05, b"\x00" * 8)
            writer.write(struct.pack("<I", len(other)) + other)
            writer.write(SERVER_INFO_REPLY)

        writer.write(struct.pack("<I", len(message)) + message)
        await writer.drain()
        writer.close()

    return await asyncio.start_server(handle, "127.0.0.1", 0)


@pytest.mark.asyncio
async def test_get_info_against_fake_server():
    received = []
    server = await _serve_info({4: _decode_captured_info()}, received)
    port = server.sockets[0].getsockname()[1]

    async with server:
        info = await TrackmaniaSunrise("127.0.0.1", port, timeout=5.0).get_info()

    assert [message_type for message_type, _ in received] == [3, 3]
    assert struct.unpack_from("<II", received[0][1]) == (4, 8)
    assert struct.unpack_from("<II", received[1][1]) == (4, 7)
    assert info.name == "Sunrise LAN Server"
    assert info.protocol_version == 4


@pytest.mark.asyncio
async def test_get_info_switches_to_nations_eswc_version():
    received = []
    server = await _serve_info({5: _server_info(game_tag=0x09)}, received)
    port = server.sockets[0].getsockname()[1]

    async with server:
        info = await TrackmaniaSunrise("127.0.0.1", port, timeout=5.0).get_info()

    assert [struct.unpack_from("<I", payload)[0] for _, payload in received] == [
        4,
        4,
        5,
        5,
    ]
    assert info.protocol_version == 5
    assert info.game_id == "TmNationsESWC"


@pytest.mark.asyncio
async def test_get_info_refused():
    received = []
    server = await _serve_info({3: b""}, received)
    port = server.sockets[0].getsockname()[1]

    async with server:
        with pytest.raises(InvalidPacketException):
            await TrackmaniaSunrise("127.0.0.1", port, timeout=5.0).get_info()


class _FakeSessionServer(asyncio.DatagramProtocol):
    """Answers session queries for one game id only, like a real server."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.queries = []

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message_type, payload = TrackmaniaSunrise.decode_message(data)
        length = struct.unpack_from("<I", payload)[0]
        game_id = payload[4 : 4 + length].decode()
        nonce = struct.unpack_from("<I", payload, len(payload) - 4)[0]
        self.queries.append((message_type, game_id))

        if game_id != self.game_id:
            return

        def string(text: str) -> bytes:
            return struct.pack("<I", len(text)) + text.encode()

        address = bytes([1, 0, 0, 127]) + struct.pack("<H", 2350)
        reply = struct.pack("<I", nonce) + string("GameNet") + string(game_id)
        reply += string("1.043") + string("LANBOX") + address + address

        self.transport.sendto(TrackmaniaSunrise.build_message(0x01, reply), addr)


@pytest.mark.asyncio
async def test_get_session_identifies_game():
    loop = asyncio.get_running_loop()
    transport, server = await loop.create_datagram_endpoint(
        lambda: _FakeSessionServer("TmOriginal"), local_addr=("127.0.0.1", 0)
    )
    port = transport.get_extra_info("sockname")[1]

    try:
        session = await TrackmaniaSunrise("127.0.0.1", port, timeout=2.0).get_session()
    finally:
        transport.close()

    # The client returns on the first reply, later queries may not be processed yet
    queried = {game_id for _, game_id in server.queries}
    assert "TmOriginal" in queried
    assert queried <= set(TrackmaniaSunrise.GAMES)
    assert {message_type for message_type, _ in server.queries} == {0}
    assert (session.game_id, session.game) == ("TmOriginal", "TrackMania Original")
    assert session.host_name == "LANBOX"


@pytest.mark.asyncio
async def test_get_session_without_matching_server():
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _FakeSessionServer("TmOriginal"), local_addr=("127.0.0.1", 0)
    )
    port = transport.get_extra_info("sockname")[1]

    try:
        with pytest.raises(ServerNotFoundException):
            await TrackmaniaSunrise("127.0.0.1", port, timeout=0.5).get_session(
                "TmSunrise"
            )
    finally:
        transport.close()
