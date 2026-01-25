from dataclasses import dataclass


@dataclass
class Info:
    """
    Represents the info response from an Unreal Tournament 2004 server.
    """

    hostname: str = ""
    """Server hostname."""

    hostport: str = ""
    """Server hostport."""

    maptitle: str = ""
    """Current map title."""

    mapname: str = ""
    """Current map name."""

    gametype: str = ""
    """Game type."""

    numplayers: str = ""
    """Current number of players."""

    maxplayers: str = ""
    """Maximum number of players."""

    gamemode: str = ""
    """Game mode."""

    gamever: str = ""
    """Game version."""

    minnetver: str = ""
    """Minimum network version."""

    queryid: str = ""
    """Query ID."""

    def __init__(self, data: dict[str, str]):
        """
        Initialize Info object from parsed data dictionary.

        :param data: Dictionary containing server information
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
