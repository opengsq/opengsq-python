from enum import IntEnum


class VAC(IntEnum):
    """
    Specifies whether the server uses VAC.
    """

    Unsecured = 0
    """Unsecured"""

    Secured = 1
    """Secured"""
