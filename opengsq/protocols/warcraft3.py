from __future__ import annotations

from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.binary_reader import BinaryReader
from opengsq.responses.warcraft3 import Status
from enum import IntFlag, IntEnum

class GameFlags(IntFlag):
    """Game flags based on the Go implementation"""
    CUSTOM_GAME = 0x000001
    SINGLE_PLAYER = 0x000005
    LADDER_1V1 = 0x000010
    LADDER_2V2 = 0x000020
    LADDER_3V3 = 0x000040
    LADDER_4V4 = 0x000080
    TEAM_LADDER = 0x000020
    SAVED_GAME = 0x000200
    TYPE_MASK = 0x0002F5
    SIGNED_MAP = 0x000008
    PRIVATE_GAME = 0x000800
    CREATOR_USER = 0x002000
    CREATOR_BLIZZARD = 0x004000
    CREATOR_MASK = 0x006000
    MAP_TYPE_MELEE = 0x008000
    MAP_TYPE_SCENARIO = 0x010000
    MAP_TYPE_MASK = 0x018000
    SIZE_SMALL = 0x020000
    SIZE_MEDIUM = 0x040000
    SIZE_LARGE = 0x080000
    SIZE_MASK = 0x0E0000
    OBS_FULL = 0x100000
    OBS_ON_DEFEAT = 0x200000
    OBS_NONE = 0x400000
    OBS_MASK = 0x700000
    FILTER_MASK = 0x7FE000

class GameSettingFlags(IntFlag):
    """Game setting flags based on the Go implementation"""
    SPEED_SLOW = 0x00000000
    SPEED_NORMAL = 0x00000001
    SPEED_FAST = 0x00000002
    SPEED_MASK = 0x0000000F
    TERRAIN_HIDDEN = 0x00000100
    TERRAIN_EXPLORED = 0x00000200
    TERRAIN_VISIBLE = 0x00000400
    TERRAIN_DEFAULT = 0x00000800
    TERRAIN_MASK = 0x00000F00
    OBS_NONE = 0x00000000
    OBS_ENABLED = 0x00001000
    OBS_ON_DEFEAT = 0x00002000
    OBS_FULL = 0x00003000
    OBS_REFEREES = 0x40000000
    OBS_MASK = 0x40003000
    TEAMS_TOGETHER = 0x00004000
    TEAMS_FIXED = 0x00060000
    SHARED_CONTROL = 0x01000000
    RANDOM_HERO = 0x02000000
    RANDOM_RACE = 0x04000000

class SlotStatus(IntEnum):
    """Slot status based on the Go implementation"""
    OPEN = 0x00
    CLOSED = 0x01
    OCCUPIED = 0x02

class Warcraft3(ProtocolBase):
    """
    This class represents the Warcraft 3 Protocol. It provides methods to interact with Warcraft 3 game servers.
    Based on the gowarcraft3 implementation.
    """

    full_name = "Warcraft 3 Protocol"
    WARCRAFT3_PORT = 6112  # Default port for Warcraft 3
    PROTOCOL_SIG = 0xF7  # Protocol signature
    CURRENT_GAME_VERSION = 26  # Current game version (changed from 10032 to 26)

    # Packet types
    PID_SEARCH_GAME = 0x2F
    PID_GAME_INFO = 0x30

    def __init__(self, host: str, port: int = WARCRAFT3_PORT, timeout: float = 5.0):
        """
        Initialize the Warcraft 3 protocol handler.

        :param host: The server address
        :param port: The port to use (default: 6112)
        :param timeout: Connection timeout in seconds
        """
        if port != self.WARCRAFT3_PORT:
            raise ValueError(f"Warcraft 3 protocol requires port {self.WARCRAFT3_PORT}")
        super().__init__(host, self.WARCRAFT3_PORT, timeout)

    def _create_search_game_packet(self) -> bytes:
        """Creates a search game packet based on the Go implementation"""
        packet = bytearray()
        packet.extend([
            self.PROTOCOL_SIG,  # Protocol signature
            self.PID_SEARCH_GAME,  # Packet type
            0x10, 0x00,  # Packet size (16 bytes)
            0x50, 0x58, 0x33, 0x57,  # Product "PX3W" (reversed "W3XP")
            # Game version (little endian)
            self.CURRENT_GAME_VERSION & 0xFF,
            (self.CURRENT_GAME_VERSION >> 8) & 0xFF,
            (self.CURRENT_GAME_VERSION >> 16) & 0xFF,
            (self.CURRENT_GAME_VERSION >> 24) & 0xFF,
            # Host counter
            0x00, 0x00, 0x00, 0x00
        ])
        return bytes(packet)

    async def get_status(self) -> Status:
        """
        Asynchronously retrieves the status of the game server.

        :return: A Status object containing the status of the game server.
        """
        request = self._create_search_game_packet()
        response = await UdpClient.communicate(self, request, source_port=self.WARCRAFT3_PORT)

        if not response or len(response) < 4:
            raise Exception("Invalid response")

        br = BinaryReader(response)
        
        # Validate protocol signature
        if int.from_bytes(br.read_bytes(1), 'little') != self.PROTOCOL_SIG:
            raise Exception("Invalid protocol signature")

        # Validate packet type
        if int.from_bytes(br.read_bytes(1), 'little') != self.PID_GAME_INFO:
            raise Exception("Invalid response packet type")

        # Read packet size
        packet_size = int.from_bytes(br.read_bytes(2), 'little')
        if len(response) < packet_size:
            raise Exception("Incomplete response")

        # Read game version info
        product = br.read_bytes(4).decode('ascii')  # Product code (WAR3/W3XP)
        version = int.from_bytes(br.read_bytes(4), 'little')  # Game version
        host_counter = int.from_bytes(br.read_bytes(4), 'little')  # Host counter
        entry_key = int.from_bytes(br.read_bytes(4), 'little')  # Entry key

        # Read game name (null-terminated)
        game_name = ""
        while True:
            char = int.from_bytes(br.read_bytes(1), 'little')
            if char == 0:
                break
            game_name += chr(char)

        # Skip unknown byte
        br.read_bytes(1)

        # Read game settings string (null-terminated)
        settings_raw = bytearray()
        while True:
            byte = int.from_bytes(br.read_bytes(1), 'little')
            if byte == 0:
                break
            settings_raw.append(byte)

        # Read remaining fields
        slots_total = int.from_bytes(br.read_bytes(4), 'little')
        game_flags = GameFlags(int.from_bytes(br.read_bytes(4), 'little'))
        slots_used = int.from_bytes(br.read_bytes(4), 'little')
        slots_available = int.from_bytes(br.read_bytes(4), 'little')
        uptime_seconds = int.from_bytes(br.read_bytes(4), 'little')
        port = int.from_bytes(br.read_bytes(2), 'little')

        # Store raw data for debugging
        raw = {
            'product': product,
            'version': version,
            'host_counter': host_counter,
            'entry_key': entry_key,
            'settings_raw': settings_raw.hex(),
            'game_flags': game_flags,
            'remaining_data': br.read_bytes(br.remaining_bytes()).hex()
        }

        return Status(
            game_version=f"{product} {version}",
            hostname=game_name,
            map_name=self._get_map_name_from_settings(settings_raw),
            game_type=self._get_game_type(game_flags),
            num_players=slots_used,
            max_players=slots_total,
            raw=raw
        )

    def _get_map_name_from_settings(self, settings_raw: bytearray) -> str:
        """Map name parsing is skipped due to encoding complexity"""
        return "Map name unavailable"

    def _get_game_type(self, flags: GameFlags) -> str:
        """Convert game flags to a readable game type"""
        if flags & GameFlags.CUSTOM_GAME:
            return "Custom Game"
        elif flags & GameFlags.SINGLE_PLAYER:
            return "Single Player"
        elif flags & GameFlags.LADDER_1V1:
            return "Ladder 1v1"
        elif flags & GameFlags.LADDER_2V2:
            return "Ladder 2v2"
        elif flags & GameFlags.LADDER_3V3:
            return "Ladder 3v3"
        elif flags & GameFlags.LADDER_4V4:
            return "Ladder 4v4"
        elif flags & GameFlags.SAVED_GAME:
            return "Saved Game"
        return "Unknown" 