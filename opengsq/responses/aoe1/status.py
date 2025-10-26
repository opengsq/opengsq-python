from __future__ import annotations
from dataclasses import dataclass
from typing import List
from opengsq.responses.directplay.status import Status as DirectPlayStatus


@dataclass
class Status(DirectPlayStatus):
    """Age of Empires 1 specific status response"""
    
    # AoE1 spezifische Felder
    epoch: str = "Stone Age"  # Stone Age, Tool Age, Bronze Age, Iron Age
    population_limit: int = 50
    resources_setting: str = "Standard"  # Low, Standard, High
    reveal_map: bool = False
    starting_resources: str = "Standard"
    victory_conditions: List[str] = None  # Standard, Conquest, Ruins, Artifacts
    
    def __post_init__(self):
        if self.victory_conditions is None:
            self.victory_conditions = ["Conquest"]
