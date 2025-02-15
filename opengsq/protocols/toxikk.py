from opengsq.protocols.udk import UDK
from opengsq.responses.toxikk.status import Status

class Toxikk(UDK):
    GAMEMODE_NAMES = {
        "cruzade.CRZBloodLust": "BloodLust",
        "cruzade.CRZTeamGame": "Squad Assault", 
        "cruzade.CRZSquadSurvival": "Squad Survival",
        "cruzade.CRZCellCapture": "Cell Capture",
        "cruzade.CRZAreaDomination": "Area Domination",
        "cruzade.CRZArchRivals": "Arch Rivals"
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

    full_name = "Toxikk Protocol"
    
    def __init__(self, host: str, port: int = 14001, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self.game_id = 0x4D5707DB
        self.packet_version = 7

    def _parse_response(self, buffer: bytes) -> dict:
        base_response = super()._parse_response(buffer)
        toxikk_properties = {}

        for prop in base_response['raw']['settings_properties']:
            prop_id = prop['id']
            if prop_id == 1073741825:      # Map
                base_response['map'] = prop['data']
                toxikk_properties['map'] = prop['data']
            elif prop_id == 1073741826:     # Game Type
                base_response['game_type'] = prop['data']
                toxikk_properties['gametype'] = self.GAMEMODE_NAMES.get(prop['data'], prop['data'])
            elif prop_id == 268435704:      # Frag Limit
                toxikk_properties['frag_limit'] = prop['data']
            elif prop_id == 268435705:      # Time Limit
                toxikk_properties['time_limit'] = prop['data']
            elif prop_id == 268435703:      # Number of Bots
                toxikk_properties['numbots'] = prop['data']
            elif prop_id == 1073741828:     # Mutators
                toxikk_properties['mutators'] = self._parse_mutators(prop['data'])

        for setting in base_response['raw']['localized_settings']:
            setting_id = setting['id']
            value_index = setting['value_index']
            
            if setting_id == 0:
                toxikk_properties['bot_skill'] = self.BOT_SKILL_NAMES.get(value_index)
            elif setting_id == 6:
                toxikk_properties['pure_server'] = value_index
            elif setting_id == 7:
                base_response['password_protected'] = value_index == 1
                toxikk_properties['password'] = value_index
            elif setting_id == 8:
                toxikk_properties['vs_bots'] = self.VS_BOTS_NAMES.get(value_index)
            elif setting_id == 10:
                toxikk_properties['force_respawn'] = value_index

        base_response['raw'].update(toxikk_properties)
        return base_response

    def _parse_mutators(self, mutator_value: any) -> list:
        if not mutator_value or not isinstance(mutator_value, str):
            return []
        return [m.title() for m in mutator_value.split('\x1c') if m]