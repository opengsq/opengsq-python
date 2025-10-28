from __future__ import annotations
from dataclasses import dataclass
from typing import List
from opengsq.responses.directplay.status import Status as DirectPlayStatus


@dataclass
class Status(DirectPlayStatus):
    """Age of Empires 2 specific status response"""

    # AoE2 spezifische Felder
    age: str = "Dark Age"  # Dark Age, Feudal Age, Castle Age, Imperial Age
    population_limit: int = 200
    starting_age: str = "Dark Age"
    resources_setting: str = "Standard"  # Low, Standard, High
    reveal_map: bool = False
    map_size: str = "Normal"  # Tiny, Small, Normal, Large, Giant
    victory_conditions: List[str] = None  # Standard, Conquest, Relics, Wonder, Time
    teams_locked: bool = False
    all_techs: bool = False

    def __post_init__(self):
        if self.victory_conditions is None:
            self.victory_conditions = ["Conquest"]
