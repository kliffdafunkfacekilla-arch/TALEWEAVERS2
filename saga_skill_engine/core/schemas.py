from pydantic import BaseModel, Field
from typing import Optional

class RollState(BaseModel):
    is_advantage: bool = False
    is_disadvantage: bool = False
    focus_spent: int = 0       # Players can burn Focus to add dice/bonuses

class SkillCheckRequest(BaseModel):
    character_id: str
    triad_name: str            # e.g., "Awareness + Intuition"
    lead_stat_value: int
    trail_stat_value: int
    skill_rank: int            # 0 to 5
    target_dc: int
    roll_state: RollState
    is_life_or_death: bool = False # GM toggles this to allow "Survivor" pips

class SkillCheckResult(BaseModel):
    roll_total: int
    raw_die_face: int          # Needed to check for Nat 1s and Nat 20s
    is_success: bool
    margin: int
    scars_and_stars_trigger: Optional[str] = None # "STAR", "SCAR", "SURVIVOR", or None
