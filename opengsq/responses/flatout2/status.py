from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Status:
    """
    Represents the status of a Flatout 2 server.
    """

    info: Dict[str, str]
    """
    Server information dictionary containing:
    - hostname: Server name (UTF-16 encoded)
    - timestamp: Server timestamp
    - flags: Server configuration flags
    - status: Server status flags
    - config: Additional configuration data in hex format
    """

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the server status.
        
        :return: Formatted server status string
        """
        result = []
        
        # Add server info
        result.append("Server Information:")
        for key, value in self.info.items():
            result.append(f"  {key}: {value}")
        
        return "\n".join(result) 