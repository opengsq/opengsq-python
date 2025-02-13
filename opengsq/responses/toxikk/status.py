from __future__ import annotations
from dataclasses import dataclass
from typing import List
from opengsq.responses.udk.status import Status as UDKStatus

@dataclass
class Status(UDKStatus):
    """Toxikk-specific status response"""
    mutators: List[str] = None