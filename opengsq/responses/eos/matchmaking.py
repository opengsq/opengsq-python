from __future__ import annotations
from typing import Any
from dataclasses import dataclass


@dataclass
class Matchmaking:
    """
    Represents the response from a matchmaking request.
    """

    sessions: list[dict[str, Any]]
    """The list of sessions returned by the matchmaking request.
    Each session is represented as a dictionary of string keys and object values."""

    count: int
    """The count of sessions returned by the matchmaking request."""
