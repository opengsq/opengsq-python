from dataclasses import dataclass, field


@dataclass
class Status:
    """
    Represents the full status response from an Unreal Tournament 2004 server.
    """

    info: dict[str, str] = field(default_factory=dict)
    """The server info."""

    players: dict[str, str] = field(default_factory=dict)
    """The server players."""

    rules: dict[str, str] = field(default_factory=dict)
    """The server rules."""

    def __init__(self, data: dict[str, dict[str, str]]):
        """
        Initialize Status object from parsed data dictionary.

        :param data: Dictionary containing server status information
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
