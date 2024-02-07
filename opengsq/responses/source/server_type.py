from enum import IntEnum


class ServerType(IntEnum):
    """
    Indicates the type of server.
    """

    Dedicated = 0x64
    """Dedicated server"""

    Listen = 0x6C
    """Listen server"""

    Proxy = 0x70
    """SourceTV relay (proxy)"""

    @staticmethod
    def parse(byte: int):
        """
        Parses the given byte to a ServerType value. If the byte does not correspond to a valid
        ServerType value, a ValueError is raised.

        Args:
            byte (int): The byte to parse.

        Returns:
            ServerType: The corresponding ServerType value.
        """
        return ServerType(ord(chr(byte).lower()))
