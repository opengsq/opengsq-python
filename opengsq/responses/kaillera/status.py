from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Status:
    """
    Represents the status of the server.
    """

    server_name: str

    ip_address: str

    port: int

    users: int

    max_users: int

    game_count: int

    version: str

    location: str
