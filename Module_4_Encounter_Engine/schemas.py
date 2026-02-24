from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field

class EncounterType(str, Enum):
    COMBAT = "COMBAT"
    SOCIAL = "SOCIAL"
    HAZARD = "HAZARD"
    PUZZLE = "PUZZLE"
    DISCOVERY = "DISCOVERY"
    DILEMMA = "DILEMMA"

class Choice(BaseModel):
    choice: str
    cost: Dict[str, Any]
    reward: Dict[str, Any]

class EncounterBase(BaseModel):
    id: str
    name: str
    description: str
    type: EncounterType
    threat_level: int

class CombatEncounter(EncounterBase):
    type: EncounterType = EncounterType.COMBAT
    enemies: List[Dict[str, Any]]  # List of enemy names and basic stats (no math)

class SocialEncounter(EncounterBase):
    type: EncounterType = EncounterType.SOCIAL
    target_npc: str
    composure: int
    social_stakes: str

class HazardEncounter(EncounterBase):
    type: EncounterType = EncounterType.HAZARD
    hazard_type: str
    bypass_condition: str
    damage_type: str

class PuzzleEncounter(EncounterBase):
    type: EncounterType = EncounterType.PUZZLE
    mechanism: str
    difficulty_class: int
    reward_hint: str

class DiscoveryEncounter(EncounterBase):
    type: EncounterType = EncounterType.DISCOVERY
    lore_snippet: str
    hidden_item_id: Optional[str] = None

class DilemmaEncounter(EncounterBase):
    type: EncounterType = EncounterType.DILEMMA
    choices: List[Choice]

# Polymorphic Type
Encounter = Union[
    CombatEncounter,
    SocialEncounter,
    HazardEncounter,
    PuzzleEncounter,
    DiscoveryEncounter,
    DilemmaEncounter
]
