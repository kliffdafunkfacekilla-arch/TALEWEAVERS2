from pydantic import BaseModel
from typing import Optional

class CombatantState(BaseModel):
    name: str
    current_hp: int = 10         # The engine needs this to calculate trauma!
    attack_or_defense_pool: int  
    weapon_damage_dice: Optional[str] = None  
    stamina_burned: int = 0      
    focus_burned: int = 0        

class ClashRequest(BaseModel):
    attacker: CombatantState
    defender: CombatantState
    chaos_level: int = 1         

class ClashResolution(BaseModel):
    clash_result: str            
    attacker_roll: int
    defender_roll: int
    margin: int
    attacker_hp_change: int = 0
    defender_hp_change: int = 0
    attacker_injury_applied: Optional[str] = None  
    defender_injury_applied: Optional[str] = None
    stamina_deducted_attacker: int = 0
    stamina_deducted_defender: int = 0
    chaos_effect_triggered: Optional[str] = None
