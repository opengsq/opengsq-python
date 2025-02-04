from opengsq.protocols.udk import UDK
from opengsq.responses.ut3.status import Status

class UT3(UDK):
    GAMEMODE_NAMES = {
        0: "Deathmatch",
        1: "Team Deathmatch", 
        2: "Capture The Flag",
        3: "Vehicle CTF",
        4: "Warfare",
        5: "Duel",
        6: "Campaign",
        7: "Greed",
        8: "Betrayal",
        9: "Custom"
    }

    MUTATOR_NAMES = {
        0x1: "SlowTimeKills",
        0x2: "BigHead",
        0x4: "NoOrbs",
        0x8: "FriendlyFire", 
        0x10: "Handicap",
        0x20: "Instagib",
        0x40: "LowGrav",
        0x80: "NoPowerups",
        0x100: "NoTranslocator",
        0x200: "Slomo",
        0x400: "SpeedFreak",
        0x800: "SuperBerserk",
        0x1000: "WeaponReplacement",
        0x2000: "WeaponsRespawn",
        0x4000: "Survival",
        0x8000: "Hero",
        0x10000: "Arena"
    }

    BOT_SKILL_NAMES = {
    0: "Novice",
    1: "Average", 
    2: "Experienced",
    3: "Skilled",
    4: "Adept",
    5: "Masterful",
    6: "Inhuman",
    7: "Godlike"
    }

    VS_BOTS_NAMES = {
    0: "None",
    1: "1:1",
    2: "3:2", 
    3: "2:1"
    }

    full_name = "Unreal Tournament 3 Protocol"
    
    def __init__(self, host: str, port: int = 14001, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self.game_id = 0x4D5707DB

    def _parse_response(self, buffer: bytes) -> dict:
        base_response = super()._parse_response(buffer)
        
        # Process properties
        ut3_properties = {}
        for prop in base_response['raw']['settings_properties']:
            prop_id = prop['id']
            if prop_id == 1073741825:      # Map
                base_response['map'] = prop['data']
                ut3_properties['map'] = prop['data']
            elif prop_id == 1073741826:     # Game Type
                base_response['game_type'] = prop['data']
                ut3_properties['gametype'] = prop['data']
            elif prop_id == 268435704:      # Frag Limit
                ut3_properties['frag_limit'] = prop['data']
            elif prop_id == 268435705:      # Time Limit
                ut3_properties['time_limit'] = prop['data']
            elif prop_id == 268435703:      # Number of Bots
                ut3_properties['numbots'] = prop['data']
            if prop_id == 268435717:  # Stock Mutators
                ut3_properties['stock_mutators'] = self._parse_mutators(prop['data'])
            elif prop_id == 1073741828:  # Custom Mutators
                ut3_properties['custom_mutators'] = self._parse_mutators(prop['data'])

        # Process localized settings
        for setting in base_response['raw']['localized_settings']:
            setting_id = setting['id']
            value_index = setting['value_index']
            
            if setting_id == 32779:  # Game Mode
                ut3_properties['gamemode'] = self.GAMEMODE_NAMES.get(value_index, f"Unknown_{value_index}")
            elif setting_id == 0:
                ut3_properties['bot_skill'] = self.BOT_SKILL_NAMES.get(value_index)
            elif setting_id == 6:
                ut3_properties['pure_server'] = value_index
            elif setting_id == 7:
                base_response['password_protected'] = value_index == 1
                ut3_properties['password'] = value_index
            elif setting_id == 8:
                ut3_properties['vs_bots'] = self.VS_BOTS_NAMES.get(value_index)
            elif setting_id == 10:
                ut3_properties['force_respawn'] = value_index

        base_response['raw'].update(ut3_properties)
        return base_response

    def _parse_mutators(self, mutator_value: any) -> list:
        if not mutator_value:
            return []
        try:
            int_value = int(mutator_value)
            return [name for flag, name in self.MUTATOR_NAMES.items() if int_value & flag]
        except (ValueError, TypeError):
            return []