from enum import IntEnum


class Visibility(IntEnum):
    """
    Indicates whether the server requires a password.
    """

    Public = 0
    """Public"""

    Private = 1
    """Private"""
