from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class Status:
    """
    Represents the status response from a Flatout 2 server.
    Contains server information and player data.
    """
    info: Dict[str, Any]
    players: List[Dict[str, Any]]

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the server status.
        """
        output = ["Server Information:"]
        for key, value in self.info.items():
            output.append(f"{key}: {value}")

        if self.players:
            output.append("\nPlayers:")
            for player in self.players:
                output.append(f"{player['name']} - Score: {player['score']}")

        return "\n".join(output) 