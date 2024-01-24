from __future__ import annotations


class ExtraDataFlag(int):
    """
    Extra Data Flag (EDF)
    """

    Port = 0x80
    """Port"""

    SteamID = 0x10
    """SteamID"""

    Spectator = 0x40
    """Spectator"""

    Keywords = 0x20
    """Keywords"""

    GameID = 0x01
    """GameID"""

    def __init__(self, flags: int) -> None:
        """
        Initializes the ExtraDataFlag with the given flags.

        :param flags: The flags to initialize the ExtraDataFlag with.
        """
        super().__init__()
        self.flags = flags

    def has_flag(self, flag: int):
        """
        Checks if the ExtraDataFlag has the given flag.

        :param flag: The flag to check.
        :return: True if the ExtraDataFlag has the flag, False otherwise.
        """
        return self.flags & flag
