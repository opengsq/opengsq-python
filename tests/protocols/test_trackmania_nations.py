import asyncio
import struct

import pytest

from opengsq.exceptions import InvalidPacketException
from opengsq.protocols.trackmania_nations import TrackmaniaNations
from opengsq.responses.trackmania_nations import strip_formatting

from ..result_handler import ResultHandler

handler = ResultHandler(__file__)
handler.enable_save = True

# Test server configuration
SERVER_IP = "10.10.100.212"
SERVER_PORT = 2350

tmn = TrackmaniaNations(host=SERVER_IP, port=SERVER_PORT)

# Packets captured from a real game client and server (request id 0x00413DD5)
CLIENT_QUERY_MODE = bytes.fromhex("0e000000820399f895580700000008000000")
CLIENT_INFO_REQUEST = bytes.fromhex("1200000082033bd464400700000007000000d53d4100")
SERVER_INFO_REPLY = bytes.fromhex(
    "9b0000008303681ac2009b0000000a0700000006000000d53d41008b5c00000b2d1d641dac2e09"
    "0900000050432d636539623063050000002353525623500204000106000600094402074b617761"
    "626f6e6761075001075374616469756d0100002c6c0001ffffffff940602e09304000178030001"
    "080000004230322d526163657a710000b9020079020374040b000040070000005374616469756d"
    "110000"
)

# Server info of a dedicated server (Rounds, 15 challenges, UTF-8 comment with BOM)
DEDICATED_SERVER_INFO = bytes.fromhex(
    "2d0100007f2e090c0000004c4956452d54455354535256050000002353525623000000000006"
    "00040017000000246f2466303044474e20246666664c6976652d546573740700000053746164"
    "69756d000000001d000000efbbbf4c6976652d54657374204b6f6d6d656e74617220c3a4c3b6"
    "c3bc031e0000000f0f000000080000004230312d52616365986c0000a9070008000000423032"
    "2d526163657a710000b90200080000004230332d52616365767000002105000d000000423034"
    "2d4163726f6261746963de350000f60300080000004230352d52616365b26b00000a06000c00"
    "00004230362d4f62737461636c65f67200004d0400080000004230372d52616365be7d0000db"
    "06000d0000004230382d456e647572616e6365b8a501006f07000d0000004230392d4163726f"
    "6261746963163a00000b0600090000004231302d5370656564449d00007a0800080000004231"
    "312d52616365a4830000c60700080000004231322d526163658cb90000d104000c0000004231"
    "332d4f62737461636c65226a00009d0400090000004231342d53706565647689000048070008"
    "0000004231352d5261636540ab0000b307000100000003000000000000400700000053746164"
    "69756d"
)


def _decode_captured_info() -> bytes:
    message_type, payload = TrackmaniaNations.decode_message(SERVER_INFO_REPLY[4:])
    assert message_type == 3

    return tmn._read_info_reply(payload, 0x00413DD5)


@pytest.mark.asyncio
async def test_get_info():
    result = await tmn.get_info()
    await handler.save_result("test_get_info", result)


def test_build_requests_match_game_client():
    assert TrackmaniaNations.build_connection_admin(8) == CLIENT_QUERY_MODE
    assert (
        TrackmaniaNations.build_connection_admin(7, 0x00413DD5) == CLIENT_INFO_REQUEST
    )


def test_parse_captured_server_info():
    info = TrackmaniaNations.parse_server_info(_decode_captured_info())

    assert info.name == "Kawabonga"
    assert info.map == "B02-Race"
    assert info.environment == "Stadium"
    assert (info.players, info.max_players) == (1, 6)
    assert (info.spectators, info.max_spectators) == (0, 6)
    assert info.game_mode == "TimeAttack"
    assert info.time_limit == 300000
    assert info.password_protected is False
    assert info.spectator_password_protected is False
    assert info.ladder_mode == 0
    assert info.pack_mask == "Stadium"
    assert info.server_login == "PC-ce9b0c"
    assert (info.server_address, info.server_port) == ("172.29.100.29", 2350)
    assert info.comment == ""
    assert [(p.name, p.ladder_ranking) for p in info.player_list] == [("Kawabonga", -1)]
    assert info.nb_challenges == 1
    assert len(info.challenges) == 1
    assert info.challenges[0].gold_time == 29050
    assert info.challenges[0].copper_price == 697


def test_parse_dedicated_server_info():
    info = TrackmaniaNations.parse_server_info(DEDICATED_SERVER_INFO)

    assert info.name == "$o$f00DGN $fffLive-Test"
    assert info.plain_name == "DGN Live-Test"
    assert info.comment == "Live-Test Kommentar äöü"
    assert (info.players, info.max_players) == (0, 6)
    assert (info.spectators, info.max_spectators) == (0, 4)
    assert (info.game_mode, info.game_mode_id, info.points_limit) == ("Rounds", 3, 30)
    assert info.time_limit == 0
    assert info.player_list == []
    assert info.nb_challenges == 15
    assert [c.name for c in info.challenges[:2]] == ["B01-Race", "B02-Race"]
    assert info.challenges[7].name == "B08-Endurance"
    assert info.challenges[7].gold_time == 107960
    assert {c.environment for c in info.challenges} == {"Stadium"}
    assert info.map == "B01-Race"


def test_password_flags_from_server_login():
    data = bytearray(_decode_captured_info())
    login = data.index(b"#SRV#")
    # Replace "#SRV#" by "#SRV#f" (player and spectator password)
    data[login - 4 : login + 5] = struct.pack("<I", 6) + b"#SRV#f"

    info = TrackmaniaNations.parse_server_info(bytes(data))

    assert info.password_protected is True
    assert info.spectator_password_protected is True
    assert info.name == "Kawabonga"


def test_rejects_corrupted_checksum():
    corrupted = bytearray(SERVER_INFO_REPLY[4:])
    corrupted[-1] ^= 0xFF

    with pytest.raises(InvalidPacketException):
        TrackmaniaNations.decode_message(bytes(corrupted))


def test_rejects_other_game():
    data = bytearray(_decode_captured_info())
    data[0] = 0x2E

    with pytest.raises(InvalidPacketException):
        TrackmaniaNations.parse_server_info(bytes(data))


def test_rejects_truncated_server_info():
    with pytest.raises(InvalidPacketException):
        TrackmaniaNations.parse_server_info(_decode_captured_info()[:60])


def test_strip_formatting():
    assert strip_formatting("$o$f00Kawa$fffbonga $$5") == "Kawabonga $5"
    assert strip_formatting("$l[http://example.com]Link$l") == "Link"


@pytest.mark.asyncio
async def test_get_info_against_fake_server():
    info_data = _decode_captured_info()
    received = []

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        for _ in range(2):
            length = struct.unpack("<I", await reader.readexactly(4))[0]
            message_type, payload = TrackmaniaNations.decode_message(
                await reader.readexactly(length)
            )
            received.append((message_type, payload))

        request_id = struct.unpack_from("<I", received[1][1], 8)[0]
        reply = struct.pack("<IIII", 7, 6, request_id, len(info_data)) + info_data

        # An unrelated message and a stale reply must be skipped
        writer.write(TrackmaniaNations.build_message(0x05, b"\x00" * 8))
        writer.write(SERVER_INFO_REPLY)
        writer.write(TrackmaniaNations.build_message(0x03, reply))
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        info = await TrackmaniaNations("127.0.0.1", port, timeout=5.0).get_info()

    assert [message_type for message_type, _ in received] == [3, 3]
    assert struct.unpack_from("<II", received[0][1]) == (7, 8)
    assert struct.unpack_from("<II", received[1][1]) == (7, 7)
    assert info.name == "Kawabonga"
    assert info.map == "B02-Race"
