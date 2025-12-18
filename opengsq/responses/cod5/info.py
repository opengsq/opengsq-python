from dataclasses import dataclass


def translate_gametype(gametype_code: str) -> str:
    """
    Translate CoD5 gametype codes to German display names.

    :param gametype_code: The gametype code from the server
    :return: German display name for the gametype
    """
    gametype_translations = {
        "dm": "Death Match",
        "war": "Team Death Match",
        "dom": "Domination",
        "koth": "HQ",
        "sab": "Sabotage",
        "sd": "Search and Destroy",
        "ctf": "Capture the Flag",
    }

    return gametype_translations.get(gametype_code.lower(), gametype_code)


@dataclass
class Info:
    """
    Represents the info response from a Call of Duty 5: World at War server.
    """

    challenge: str = ""
    """Challenge string."""

    protocol: str = ""
    """Protocol version."""

    hostname: str = ""
    """Server hostname."""

    mapname: str = ""
    """Current map name."""

    clients: str = ""
    """Current clients."""

    sv_maxclients: str = ""
    """Maximum clients."""

    gametype: str = ""
    """Game type."""

    pure: str = ""
    """Pure server."""

    hw: str = ""
    """Hardware information."""

    mod: str = ""
    """Mod information."""

    voice: str = ""
    """Voice chat enabled."""

    pb: str = ""
    """PunkBuster enabled."""

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

        :return: German display name for the gametype
        """
        return translate_gametype(self.gametype)

    def __getattribute__(self, name):
        if name == "__dict__":
            # Create a custom dict that includes properties
            result = {}
            # Get the original __dict__ first
            original_dict = object.__getattribute__(self, "__dict__")
            result.update(original_dict)
            # Add the translated gametype
            result["gametype_translated"] = self.gametype_translated
            return result
        return object.__getattribute__(self, name)
