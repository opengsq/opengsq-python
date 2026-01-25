from dataclasses import dataclass


@dataclass
class Rules:
    """
    Represents the rules response from an Unreal Tournament 2004 server.
    """

    AdminName: str = ""
    """Admin Name"""

    AdminEMail: str = ""
    """Admin Email"""

    password: str = ""
    """Server Password"""

    queryid: str = ""
    """Query ID"""

    def __init__(self, data: dict[str, str]):
        """
        Initialize Rules object from parsed data dictionary.

        :param data: Dictionary containing rule information
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
