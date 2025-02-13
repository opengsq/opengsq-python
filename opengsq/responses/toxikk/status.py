from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from opengsq.responses.udk.status import Status as UDKStatus

@dataclass
class Status(UDKStatus):
    """Toxikk-specific status response"""
    mutators: List[str] = field(default_factory=list)