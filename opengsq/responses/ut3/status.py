from __future__ import annotations
from dataclasses import dataclass
from typing import List
from opengsq.responses.udk.status import Status as UDKStatus

@dataclass
class Status(UDKStatus):
    """UT3-specific status response"""
    mutators: List[str] = None
    stock_mutators: List[str] = None
    custom_mutators: List[str] = None