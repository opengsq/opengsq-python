from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.udk.status import Status, PlatformType, Player
from opengsq.binary_reader import BinaryReader
import struct
import os

class UDK(ProtocolBase):
    full_name = "UnrealEngine3/UDK Protocol"
    LAN_BEACON_PACKET_HEADER_SIZE = 16
    UDK_PORT = 14001
    
    def __init__(self, host: str, port: int = UDK_PORT, timeout: float = 5.0):
        if port != self.UDK_PORT:
            raise ValueError(f"UDK protocol requires port {self.UDK_PORT}")
        super().__init__(host, self.UDK_PORT, timeout)
        self._allow_broadcast = True
        self.packet_version = 5 
        self.game_id = 0x00000000
        self.platform = PlatformType.Windows
        self.client_nonce = os.urandom(8)
        self.packet_types_query = (b'S', b'Q')
        self.packet_types_response = (b'S', b'R')

    async def get_status(self) -> Status:
        packet = self._build_query_packet()
        data = await UdpClient.communicate(self, packet, source_port=self.UDK_PORT)
        if not self._is_valid_response(data):
            raise Exception("Invalid response")
        parsed_data = self._parse_response(data)
        return Status(**parsed_data)
    
    def _build_query_packet(self) -> bytes:
        packet = bytearray(self.LAN_BEACON_PACKET_HEADER_SIZE)
        struct.pack_into("!BB", packet, 0, self.packet_version, self.platform)
        struct.pack_into("!I", packet, 2, self.game_id)
        packet[6:7] = self.packet_types_query[0]
        packet[7:8] = self.packet_types_query[1]
        packet[8:16] = self.client_nonce
        return bytes(packet)

    def _is_valid_response(self, buffer: bytes) -> bool:
        if len(buffer) <= self.LAN_BEACON_PACKET_HEADER_SIZE:
            return False
            
        version = buffer[0]
        platform = buffer[1]
        game_id = struct.unpack("!I", buffer[2:6])[0]
        response_type = (buffer[6:7], buffer[7:8])
        response_nonce = buffer[8:16]
        
        return (version == self.packet_version and
                platform == self.platform and
                game_id == self.game_id and
                response_type == self.packet_types_response and
                response_nonce == self.client_nonce)

    def _parse_response(self, buffer: bytes) -> dict:
        br = BinaryReader(buffer[self.LAN_BEACON_PACKET_HEADER_SIZE:])
        
        # Parse IP and port
        ip = struct.unpack("!I", br.read_bytes(4))[0]
        port = struct.unpack("!I", br.read_bytes(4))[0]
        ip_str = f"{(ip >> 24) & 255}.{(ip >> 16) & 255}.{(ip >> 8) & 255}.{ip & 255}"

        # Parse connection info
        num_open_public_conn = struct.unpack("!I", br.read_bytes(4))[0]
        num_open_private_conn = struct.unpack("!I", br.read_bytes(4))[0]
        num_public_conn = struct.unpack("!I", br.read_bytes(4))[0]
        num_private_conn = struct.unpack("!I", br.read_bytes(4))[0]

        # Parse flags
        should_advertise = br.read_bytes(1)[0] == 1
        is_lan_match = br.read_bytes(1)[0] == 1
        uses_stats = br.read_bytes(1)[0] == 1
        allow_join_in_progress = br.read_bytes(1)[0] == 1
        allow_invites = br.read_bytes(1)[0] == 1
        uses_presence = br.read_bytes(1)[0] == 1
        allow_join_via_presence = br.read_bytes(1)[0] == 1
        uses_arbitration = br.read_bytes(1)[0] == 1
        
        if self.packet_version >= 5:
            anti_cheat_protected = br.read_bytes(1)[0] == 1

        # Read owner info
        owner_id = br.read_bytes(8)
        owner_name = self._read_string(br)

        # Read properties
        num_advertised_properties = struct.unpack("!I", br.read_bytes(4))[0]
        localized_settings = []
        for _ in range(num_advertised_properties):
            if br.remaining_bytes() <= 0:
                break
            setting_id = struct.unpack("!i", br.read_bytes(4))[0]
            value_index = struct.unpack("!i", br.read_bytes(4))[0]
            advertisement_type = br.read_bytes(1)[0]
            localized_settings.append({
                'id': setting_id,
                'value_index': value_index,
                'advertisement_type': advertisement_type
            })

        num_properties = struct.unpack("!I", br.read_bytes(4))[0]
        settings_properties = []
        for _ in range(num_properties):
            if br.remaining_bytes() <= 0:
                break
            property_id = struct.unpack("!I", br.read_bytes(4))[0]
            data_type = br.read_bytes(1)[0]
            data = self._read_settings_data(br, data_type)
            advertisement_type = br.read_bytes(1)[0]
            settings_properties.append({
                'id': property_id,
                'data': data,
                'advertisement_type': advertisement_type
            })

        raw = {
            'hostaddress': ip_str,
            'hostport': port,
            'num_players': num_public_conn - num_open_public_conn,
            'max_players': num_public_conn,
            'lan_mode': is_lan_match,
            'uses_stats': uses_stats,
            'owner_id': owner_id.hex(),
            'owner_name': owner_name,
            'localized_settings': localized_settings,
            'settings_properties': settings_properties
        }

        result = {
            'name': owner_name,
            'map': '',
            'game_type': '',
            'num_players': raw['num_players'],
            'max_players': raw['max_players'],
            'password_protected': False,
            'stats_enabled': uses_stats,
            'lan_mode': is_lan_match,
            'players': [],
            'raw': raw
        }

        # Map properties by ID
        for prop in settings_properties:
            if prop['id'] == 1073741825:  # Map
                result['map'] = prop['data']
            elif prop['id'] == 1073741826:  # Game Type
                result['game_type'] = prop['data']

        return result

    def _read_string(self, br: BinaryReader) -> str:
        length = struct.unpack("!i", br.read_bytes(4))[0]
        if length <= 0:
            return ""
        return br.read_bytes(length).decode('utf-8')

    def _read_settings_data(self, br: BinaryReader, data_type: int) -> any:
        if data_type == 0:  # SDT_Empty
            return None
        elif data_type == 1:  # SDT_Int32
            return struct.unpack("!i", br.read_bytes(4))[0]
        elif data_type == 2:  # SDT_Int64
            return struct.unpack("!q", br.read_bytes(8))[0]
        elif data_type == 3:  # SDT_Double
            return struct.unpack("!d", br.read_bytes(8))[0]
        elif data_type == 4:  # SDT_String
            return self._read_string(br)
        elif data_type == 5:  # SDT_Float
            return struct.unpack("!f", br.read_bytes(4))[0]
        elif data_type == 6:  # SDT_Blob
            raise NotImplementedError("Blob data type not supported")
        elif data_type == 7:  # SDT_DateTime
            return (struct.unpack("!i", br.read_bytes(4))[0], 
                   struct.unpack("!i", br.read_bytes(4))[0])  # (date, time)