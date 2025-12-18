from dataclasses import dataclass


def translate_gametype(gametype_code: str) -> str:
    """
    Translate CoD4 gametype codes to German display names.

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
    }

    return gametype_translations.get(gametype_code.lower(), gametype_code)


@dataclass
class Info:
    """
    Represents the info response from a Call of Duty 4 server.
    """

    sv_maxPing: str = ""
    """Maximum ping allowed."""

    voice: str = ""
    """Voice chat enabled."""

    mod: str = ""
    """Mod information."""

    hw: str = ""
    """Hardware information."""

    od: str = ""
    """Unknown parameter."""

    hc: str = ""
    """Hardcore mode."""

    ki: str = ""
    """Kill info."""

    ff: str = ""
    """Friendly fire."""

    pswrd: str = ""
    """Password protected."""

    shortversion: str = ""
    """Short version string."""

    build: str = ""
    """Build number."""

    pure: str = ""
    """Pure server."""

    gametype: str = ""
    """Game type."""

    sv_maxclients: str = ""
    """Maximum clients."""

    g_humanplayers: str = ""
    """Human players count."""

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
