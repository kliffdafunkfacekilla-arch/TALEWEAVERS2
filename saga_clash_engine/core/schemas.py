from pydantic import BaseModel
from typing import Optional


class CombatantState(BaseModel):
    name: str
    attack_or_defense_pool: int  # Sum of relevant stat bonuses
    weapon_damage_dice: Optional[str] = None  # e.g., "1d8+2"
    stamina_burned: int = 0      # Tactical Grit buffer spent to boost roll
    focus_burned: int = 0        # Focus spent for additional dice/bonuses


class ClashRequest(BaseModel):
    attacker: CombatantState
    defender: CombatantState
    chaos_level: int = 1         # Higher chaos = deadlocks cause wild environmental shifts


class ClashResolution(BaseModel):
    clash_result: str            # "CRUSHING_WIN", "SCRAPE", "REVERSAL", "DEADLOCK"
    attacker_roll: int
    defender_roll: int
    margin: int
    attacker_hp_change: int = 0
    defender_hp_change: int = 0
    attacker_injury_applied: Optional[str] = None  # e.g., "1 Minor Body Injury"
    defender_injury_applied: Optional[str] = None
    stamina_deducted_attacker: int = 0
    stamina_deducted_defender: int = 0
    chaos_effect_triggered: Optional[str] = None
