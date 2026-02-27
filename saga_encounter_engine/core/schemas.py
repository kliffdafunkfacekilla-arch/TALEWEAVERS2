from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Literal
from enum import Enum

class EncounterCategory(str, Enum):
    COMBAT = "COMBAT"
    SOCIAL = "SOCIAL"
    HAZARD = "HAZARD"
    PUZZLE = "PUZZLE"
    DISCOVERY = "DISCOVERY"
    DILEMMA = "DILEMMA"

# --- 1. SOCIAL SCHEMA ---
class SocialNPC(BaseModel):
    name: str
    species: str
    faction: str
    disposition: str  # "FRIENDLY", "NEUTRAL", "SUSPICIOUS", "HOSTILE"
    motives: List[str]  # e.g., ["Needs Food", "Hates the Empire"]
    composure_pool: int  # Social HP
    willpower: int
    logic: int
    awareness: int
    trade_inventory: Optional[List[str]] = []

class SocialEncounter(BaseModel):
    category: Literal[EncounterCategory.SOCIAL] = EncounterCategory.SOCIAL
    title: str
    narrative_prompt: str
    npcs: List[SocialNPC]
    environment_tags: List[str] = []

# --- 2. HAZARD / TRAP SCHEMA ---
class HazardEncounter(BaseModel):
    category: Literal[EncounterCategory.HAZARD] = EncounterCategory.HAZARD
    title: str
    narrative_prompt: str
    detection_check: Dict[str, Union[str, int]]  # {"triad": "Awareness + Logic", "dc": 14}
    disarm_check: Optional[Dict[str, Union[str, int]]] = None
    trigger_effect: Dict[str, str]  # {"damage": "3d6 Piercing", "save": "Reflexes Half", "injury": "Minor Body"}

# --- 3. DILEMMA / HARD CHOICE SCHEMA ---
class DilemmaOption(BaseModel):
    label: str
    consequence_mechanic: str  # e.g., "LOSE_2_STAMINA", "GAIN_ITEM_VAULT"
    consequence_narrative: str

class DilemmaEncounter(BaseModel):
    category: Literal[EncounterCategory.DILEMMA] = EncounterCategory.DILEMMA
    title: str
    narrative_prompt: str
    options: List[DilemmaOption]

# --- 4. COMBAT SCHEMA ---
class Combatant(BaseModel):
    name: str
    rank: str  # "Mook", "Elite", "Boss"
    hp: int
    stamina: int
    traits: List[str]
    weapons: List[str]
    armor: int

class CombatEncounter(BaseModel):
    category: Literal[EncounterCategory.COMBAT] = EncounterCategory.COMBAT
    title: str
    narrative_prompt: str
    enemies: List[Combatant]
    terrain_difficulty: int  # 1-10
    escape_dc: int

# --- 5. PUZZLE SCHEMA ---
class PuzzleEncounter(BaseModel):
    category: Literal[EncounterCategory.PUZZLE] = EncounterCategory.PUZZLE
    title: str
    narrative_prompt: str
    logic_gate: str  # e.g., "MATCH_THREE_SYMBOLS", "BURN_5_FOCUS"
    required_triad: str
    dc: int
    failure_cost: str

# --- 6. DISCOVERY SCHEMA ---
class DiscoveryEncounter(BaseModel):
    category: Literal[EncounterCategory.DISCOVERY] = EncounterCategory.DISCOVERY
    title: str
    narrative_prompt: str
    loot_tags: List[str]
    interaction_required: bool

# --- THE POLYMORPHIC UNION ---
EncounterData = Union[
    CombatEncounter, 
    SocialEncounter, 
    HazardEncounter, 
    PuzzleEncounter, 
    DiscoveryEncounter, 
    DilemmaEncounter
]

class EncounterResponse(BaseModel):
    encounter_id: str
    data: EncounterData

class EncounterRequest(BaseModel):
    # Contextual data for "No Input" generation
    biome: Optional[str] = None
    location_id: Optional[str] = None
    threat_level: int = 1
    world_id: Optional[str] = None
    faction_territory: Optional[str] = None
    
    # Override for "Detailed Prompt" generation
    forced_type: Optional[EncounterCategory] = None
    seed_prompt: Optional[str] = None
    quest_id: Optional[str] = None
    specific_tags: List[str] = []
