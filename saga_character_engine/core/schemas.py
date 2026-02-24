from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class CoreAttributes(BaseModel):
    # Sector I: Physical
    might: int = 0
    endurance: int = 0
    vitality: int = 0
    fortitude: int = 0
    reflexes: int = 0
    finesse: int = 0
    
    # Sector II: Mental
    knowledge: int = 0
    logic: int = 0
    charm: int = 0
    willpower: int = 0
    awareness: int = 0
    intuition: int = 0

class DerivedVitals(BaseModel):
    max_hp: int          # Might + Reflexes + Vitality
    max_stamina: int     # Endurance + Fortitude + Finesse
    max_composure: int   # Willpower + Logic + Awareness
    max_focus: int       # Knowledge + Charm + Intuition
    
    # Dual-Track Injury Slots
    body_injuries: List[str] = []
    mind_injuries: List[str] = []

class BiologicalEvolutions(BaseModel):
    species_base: str    # e.g., "PLANT", "AVIAN"
    head_slot: str = "Standard"
    body_slot: str = "Standard"
    arms_slot: str = "Standard"
    legs_slot: str = "Standard"
    skin_slot: str = "Standard"
    special_slot: str = "Standard"

class CharacterBuildRequest(BaseModel):
    name: str
    base_attributes: CoreAttributes
    evolutions: BiologicalEvolutions
    background_training: str = "None"
    selected_powers: List[str] = []
    equipped_loadout: Dict[str, str] = {}

class CompiledCharacterSheet(BaseModel):
    name: str
    attributes: CoreAttributes
    vitals: DerivedVitals
    evolutions: BiologicalEvolutions
    passives: List[Dict[str, str]] = []
    powers: List[str] = []
    loadout: Dict[str, str] = {}
    holding_fees: Dict[str, int] = {"stamina": 0, "focus": 0}
