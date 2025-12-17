from dataclasses import dataclass


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
class Info:
    """
    Represents the info response from a Star Wars Jedi Knight - Jedi Academy server.
    """

    fdisable: str = ""
    """Force powers disable flags."""

    wdisable: str = ""
    """Weapons disable flags."""

    truejedi: str = ""
    """True Jedi mode enabled."""

    needpass: str = ""
    """Password required."""

    gametype: str = ""
    """Game type."""

    sv_maxclients: str = ""
    """Maximum clients."""

    clients: str = ""
    """Current clients."""

    mapname: str = ""
    """Current map name."""

    hostname: str = ""
    """Server hostname."""

    protocol: str = ""
    """Protocol version."""

    challenge: str = ""
    """Challenge string."""

    def __init__(self, data: dict[str, str]):
        """
        Initialize Info object from parsed data dictionary.

        :param data: Dictionary containing server information
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def gametype_translated(self) -> str:
        """
        Get the translated gametype name.

        :return: Display name for the gametype
        """
        return translate_gametype(self.gametype)

    def __getattribute__(self, name):
        if name == '__dict__':
            # Create a custom dict that includes properties
            result = {}
            # Get the original __dict__ first
            original_dict = object.__getattribute__(self, '__dict__')
            result.update(original_dict)
            # Add the translated gametype
            result['gametype_translated'] = self.gametype_translated
            return result
        return object.__getattribute__(self, name)

