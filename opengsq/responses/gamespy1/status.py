from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the server status.
    """

    info: dict[str, str]
    """Server's info. If is_XServerQuery is True, then it includes \\info\\xserverquery\\rules\\xserverquery, else \\basic\\info\\rules\\"""

    players: list[dict[str, str]]
    """Server's players."""

    teams: list[dict[str, str]]
    """Server's teams. Only when is_x_server_query is True."""

    @property
    def is_XServerQuery(self) -> bool:
        """Indicates whether the response is XServerQuery or old response."""
        return "XServerQuery" in self.info
