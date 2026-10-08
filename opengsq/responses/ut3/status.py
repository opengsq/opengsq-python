from __future__ import annotations

from dataclasses import dataclass

from opengsq.responses.udk.status import Status as UDKStatus


@dataclass
class Status(UDKStatus):
    """UT3-specific status response"""

    mutators: list[str] = None
    stock_mutators: list[str] = None
    custom_mutators: list[str] = None
