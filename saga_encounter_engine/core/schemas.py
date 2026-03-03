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

class SpatialData(BaseModel):
    x_offset: float = 0.0  # Offset from hex center
    y_offset: float = 0.0
    footprint_radius: float = 1.0

# --- 1. SOCIAL SCHEMA ---
class SocialNPC(BaseModel):
    name: str
    species: str
    faction: str
    disposition: str  # "FRIENDLY", "NEUTRAL", "SUSPICIOUS", "HOSTILE"
    motives: List[str]
    composure_pool: int
    willpower: int
    logic: int
    awareness: int
    trade_inventory: Optional[List[str]] = []
    spatial: SpatialData = Field(default_factory=SpatialData)
    tags: List[str] = [] # New: Semantic tags

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
    detection_check: Dict[str, Union[str, int]]
    disarm_check: Optional[Dict[str, Union[str, int]]] = None
    trigger_effect: Dict[str, str]
    spatial: SpatialData = Field(default_factory=SpatialData)
    environmental_tags: List[str] = []
    grid: Optional[List[List[str]]] = None
    grid_width: int = 15
    grid_height: int = 10

# --- 3. DILEMMA / HARD CHOICE SCHEMA ---
class DilemmaOption(BaseModel):
    label: str
    consequence_mechanic: str
    consequence_narrative: str

class DilemmaEncounter(BaseModel):
    category: Literal[EncounterCategory.DILEMMA] = EncounterCategory.DILEMMA
    title: str
    narrative_prompt: str
    options: List[DilemmaOption]
    environmental_tags: List[str] = [] # Added

# --- 4. COMBAT SCHEMA ---
class Combatant(BaseModel):
    name: str
    rank: str
    hp: int
    stamina: int
    traits: List[str]
    weapons: List[str]
    armor: int
    spatial: SpatialData = Field(default_factory=SpatialData)
    tags: List[str] = [] # New: Semantic tags (climbable, flammable, etc.)

class CombatEncounter(BaseModel):
    category: Literal[EncounterCategory.COMBAT] = EncounterCategory.COMBAT
    title: str
    narrative_prompt: str
    enemies: List[Combatant]
    terrain_difficulty: int
    escape_dc: int
    environmental_tags: List[str] = []
    grid: Optional[List[List[str]]] = None
    grid_width: int = 15
    grid_height: int = 10

# --- 5. PUZZLE SCHEMA ---
class PuzzleEncounter(BaseModel):
    category: Literal[EncounterCategory.PUZZLE] = EncounterCategory.PUZZLE
    title: str
    narrative_prompt: str
    logic_gate: str
    required_triad: str
    dc: int
    failure_cost: str
    spatial: SpatialData = Field(default_factory=SpatialData)
    environmental_tags: List[str] = [] # Added

# --- 6. DISCOVERY SCHEMA ---
class DiscoveryEncounter(BaseModel):
    category: Literal[EncounterCategory.DISCOVERY] = EncounterCategory.DISCOVERY
    title: str
    narrative_prompt: str
    loot_tags: List[str]
    interaction_required: bool
    spatial: SpatialData = Field(default_factory=SpatialData)
    environmental_tags: List[str] = [] # Added

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
    biome: Optional[str] = None
    location_id: Optional[str] = None
    threat_level: int = 1
    world_id: Optional[str] = None
    faction_territory: Optional[str] = None
    forced_type: Optional[EncounterCategory] = None
    seed_prompt: Optional[str] = None
    quest_id: Optional[str] = None
    specific_tags: List[str] = []
