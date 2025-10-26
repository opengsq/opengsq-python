from dataclasses import dataclass


def translate_gametype(gametype_code: str) -> str:
    """
    Translate CoD5 gametype codes to German display names.
    
    :param gametype_code: The gametype code from the server
    :return: German display name for the gametype
    """
    gametype_translations = {
        'dm': 'Death Match',
        'tdm': 'Team Death Match',
        'dom': 'Domination',
        'koth': 'HQ',
        'sab': 'Sabotage',
        'sd': 'Search and Destroy',
        'twar': 'War (Capture the Flag)'
    }
    
    return gametype_translations.get(gametype_code.lower(), gametype_code)


@dataclass
class Status:
    """
    Represents the status response from a Call of Duty 5: World at War server.
    """

    fxfrustumCutoff: str = ""
    """FX frustum cutoff setting."""

    g_compassShowEnemies: str = ""
    """Compass show enemies setting."""

    g_gametype: str = ""
    """Game type."""

    gamename: str = ""
    """Game name."""

    mapname: str = ""
    """Current map name."""

    penetrationCount: str = ""
    """Penetration count setting."""

    protocol: str = ""
    """Protocol version."""

    r_watersim_enabled: str = ""
    """Water simulation enabled."""

    shortversion: str = ""
    """Short version string."""

    sv_allowAnonymous: str = ""
    """Allow anonymous players."""

    sv_disableClientConsole: str = ""
    """Client console disabled."""

    sv_floodprotect: str = ""
    """Flood protection."""

    sv_hostname: str = ""
    """Server hostname."""

    sv_maxclients: str = ""
    """Maximum clients."""

    sv_maxPing: str = ""
    """Maximum ping."""

    sv_maxRate: str = ""
    """Maximum rate."""

    sv_minPing: str = ""
    """Minimum ping."""

    sv_privateClients: str = ""
    """Private clients."""

    sv_punkbuster: str = ""
    """PunkBuster enabled."""

    sv_pure: str = ""
    """Pure server."""

    sv_voice: str = ""
    """Voice chat."""

    ui_maxclients: str = ""
    """UI maximum clients."""

    pswrd: str = ""
    """Password protected."""

    mod: str = ""
    """Mod information."""

    def __init__(self, data: dict[str, str]):
        """
        Initialize Status object from parsed data dictionary.
        
        :param data: Dictionary containing server status information
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def g_gametype_translated(self) -> str:
        """
        Get the translated gametype name.
        
        :return: German display name for the gametype
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
