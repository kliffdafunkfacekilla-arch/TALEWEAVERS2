import sys
from pathlib import Path
# Add root to sys.path to allow importing from saga_common
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from saga_common.models.core import CoreAttributes, DerivedVitals

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
