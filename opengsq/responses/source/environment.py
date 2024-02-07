from enum import IntEnum


class Environment(IntEnum):
    """
    Indicates the operating system of the server.
    """

    Linux = 0x6C
    """Linux"""

    Windows = 0x77
    """Windows"""

    Mac = 0x6D
    """Mac"""

    @staticmethod
    def parse(byte: int):
        """
        Parses the given byte to an Environment value. If the byte does not correspond to a valid
        Environment value, it defaults to Environment.Mac.

        Args:
            byte (int): The byte to parse.

        Returns:
            Environment: The corresponding Environment value, or Environment.Mac if the byte is not valid.
        """
        try:
            return Environment(ord(chr(byte).lower()))
        except ValueError:
            # 'm' or 'o' for Mac (the code changed after L4D1)
            return Environment.Mac
