from dataclasses import dataclass


def translate_gametype(gametype_code: str) -> str:
    """
    Translate CoD1 gametype codes to German display names.
    
    :param gametype_code: The gametype code from the server
    :return: German display name for the gametype
    """
    gametype_translations = {
        'dm': 'Death Match',
        'war': 'Team Death Match',
        'dom': 'Domination',
        'koth': 'HQ',
        'sab': 'Sabotage',
        'sd': 'Search and Destroy'
    }
    
    return gametype_translations.get(gametype_code.lower(), gametype_code)


@dataclass
class Status:
    """
    Represents the status response from a Call of Duty 1 server.
    """

    sv_maxclients: str = ""
    """Maximum clients."""

    version: str = ""
    """Server version."""

    shortversion: str = ""
    """Short version string."""

    build: str = ""
    """Build number."""

    branch: str = ""
    """Branch information."""

    revision: str = ""
    """Revision information."""

    _CoD4_X_Site: str = ""
    """CoD4X site information."""

    protocol: str = ""
    """Protocol version."""

    sv_privateClients: str = ""
    """Private clients."""

    sv_hostname: str = ""
    """Server hostname."""

    sv_minPing: str = ""
    """Minimum ping."""

    sv_maxPing: str = ""
    """Maximum ping."""

    sv_disableClientConsole: str = ""
    """Client console disabled."""

    sv_voice: str = ""
    """Voice chat."""

    g_mapStartTime: str = ""
    """Map start time."""

    uptime: str = ""
    """Server uptime."""

    g_gametype: str = ""
    """Game type."""

    mapname: str = ""
    """Current map name."""

    sv_maxRate: str = ""
    """Maximum rate."""

    sv_floodprotect: str = ""
    """Flood protection."""

    sv_pure: str = ""
    """Pure server."""

    gamename: str = ""
    """Game name."""

    g_compassShowEnemies: str = ""
    """Compass show enemies."""

    _Admin: str = ""
    """Admin information."""

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




