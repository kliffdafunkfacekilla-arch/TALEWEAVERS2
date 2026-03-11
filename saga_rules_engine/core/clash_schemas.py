import sys
from pathlib import Path
# Add root to sys.path to allow importing from saga_common
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from pydantic import BaseModel
from typing import Optional
from saga_common.models.core import CombatantState

class ClashRequest(BaseModel):
    attacker: CombatantState
    defender: CombatantState
    chaos_level: int = 1         
    attacker_advantage: bool = False
    attacker_disadvantage: bool = False
    defender_advantage: bool = False
    defender_disadvantage: bool = False

class ClashResolution(BaseModel):
    clash_result: str            
    attacker_roll: int
    defender_roll: int
    margin: int
    attacker_hp_change: int = 0
    defender_hp_change: int = 0
    attacker_composure_change: int = 0
    defender_composure_change: int = 0
    attacker_injury_applied: Optional[str] = None  
    defender_injury_applied: Optional[str] = None
    stamina_deducted_attacker: int = 0
    stamina_deducted_defender: int = 0
    chaos_effect_triggered: Optional[str] = None
