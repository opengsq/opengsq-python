from __future__ import annotations
from dataclasses import dataclass
from opengsq.responses.directplay.status import Status as DirectPlayStatus


@dataclass
class Status(DirectPlayStatus):
    """Stronghold Crusader specific status response"""

    # Stronghold Crusader spezifische Felder können hier hinzugefügt werden
    # wenn weitere Informationen aus dem Spiel extrahiert werden können
    pass
