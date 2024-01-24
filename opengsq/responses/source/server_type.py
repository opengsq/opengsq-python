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
