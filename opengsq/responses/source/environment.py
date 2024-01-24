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
