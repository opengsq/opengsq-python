from dataclasses import dataclass, field
from typing import List


def translate_gametype(gametype_code: str) -> str:
    """
    Translate Jedi Academy gametype codes to display names.

    :param gametype_code: The gametype code from the server
    :return: Display name for the gametype
    """
    gametype_translations = {
        '0': 'Free For All',
        '3': 'Duel',
        '4': 'Power Duel',
        '6': 'Team FFA',
        '7': 'Siege',
        '8': 'Capture the Flag',
    }

    return gametype_translations.get(str(gametype_code), gametype_code)


@dataclass
class Player:
    """
    Represents a player on a Jedi Academy server.
    """
    score: int = 0
    """Player score."""

    ping: int = 0
    """Player ping."""

    name: str = ""
    """Player name."""


@dataclass
class Status:
    """
    Represents the status response from a Star Wars Jedi Knight - Jedi Academy server.
    """

    challenge: str = ""
    """Challenge string."""

    capturelimit: str = ""
    """Capture limit for CTF."""

    sv_hostname: str = ""
    """Server hostname."""

    sv_maxRate: str = ""
    """Maximum rate."""

    sv_minPing: str = ""
    """Minimum ping."""

    sv_maxPing: str = ""
    """Maximum ping."""

    sv_floodProtect: str = ""
    """Flood protection."""

    g_siegeTeamSwitch: str = ""
    """Siege team switch."""

    version: str = ""
    """Server version."""

    dmflags: str = ""
    """Deathmatch flags."""

    fraglimit: str = ""
    """Frag limit."""

    timelimit: str = ""
    """Time limit."""

    g_maxHolocronCarry: str = ""
    """Maximum holocrons to carry."""

    g_privateDuel: str = ""
    """Private duel enabled."""

    g_saberLocking: str = ""
    """Saber locking enabled."""

    g_maxForceRank: str = ""
    """Maximum force rank."""

    duel_fraglimit: str = ""
    """Duel frag limit."""

    g_forceBasedTeams: str = ""
    """Force based teams."""

    g_duelWeaponDisable: str = ""
    """Duel weapon disable."""

    g_gametype: str = ""
    """Game type."""

    g_needpass: str = ""
    """Password required."""

    protocol: str = ""
    """Protocol version."""

    mapname: str = ""
    """Current map name."""

    sv_privateClients: str = ""
    """Private clients."""

    sv_maxclients: str = ""
    """Maximum clients."""

    sv_allowDownload: str = ""
    """Allow downloads."""

    bot_minplayers: str = ""
    """Minimum bot players."""

    g_debugMelee: str = ""
    """Debug melee."""

    g_stepSlideFix: str = ""
    """Step slide fix."""

    g_noSpecMove: str = ""
    """No spectator movement."""

    gamename: str = ""
    """Game name (basejka for base game)."""

    g_maxGameClients: str = ""
    """Maximum game clients."""

    g_jediVmerc: str = ""
    """Jedi vs Merc mode."""

    g_allowNPC: str = ""
    """Allow NPCs."""

    g_forceRegenTime: str = ""
    """Force regeneration time."""

    g_forcePowerDisable: str = ""
    """Force power disable flags."""

    g_weaponDisable: str = ""
    """Weapon disable flags."""

    g_siegeRespawn: str = ""
    """Siege respawn time."""

    g_saberWallDamageScale: str = ""
    """Saber wall damage scale."""

    bg_fighterAltControl: str = ""
    """Fighter alt control."""

    g_siegeTeam1: str = ""
    """Siege team 1."""

    g_siegeTeam2: str = ""
    """Siege team 2."""

    g_showDuelHealths: str = ""
    """Show duel healths."""

    players: List[Player] = field(default_factory=list)
    """List of players on the server."""

    def __init__(self, data: dict[str, str], players: List[Player] = None):
        """
        Initialize Status object from parsed data dictionary.

        :param data: Dictionary containing server status information
        :param players: List of players on the server
        """
        for key, value in data.items():
            # Handle potential typos in server response
            if key == 'g_saberWeallDamageScale':
                setattr(self, 'g_saberWallDamageScale', value)
            elif key == 'g_debugeMelee':
                setattr(self, 'g_debugMelee', value)
            elif hasattr(self, key):
                setattr(self, key, value)

        self.players = players if players is not None else []

    @property
    def g_gametype_translated(self) -> str:
        """
        Get the translated gametype name.

        :return: Display name for the gametype
        """
        return translate_gametype(self.g_gametype)

    def __getattribute__(self, name):
        if name == '__dict__':
            # Create a custom dict that includes properties
            result = {}
            # Get the original __dict__ first
            original_dict = object.__getattribute__(self, '__dict__')
            result.update(original_dict)
            # Add the translated gametype
            result['g_gametype_translated'] = self.g_gametype_translated
            return result
        return object.__getattribute__(self, name)

