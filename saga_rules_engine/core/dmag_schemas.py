from pydantic import BaseModel
from typing import Optional, Dict, List

class SpellCastRequest(BaseModel):
    spell_name: str
    school: str
    base_intensity: int
    character_stats: Dict[str, int]
    environment_context: Dict[str, str] # e.g., {"biome": "Jungle", "weather": "Rain"}
    dust_amount: int = 0
    chaos_level: int = 1

class SpellCastResolution(BaseModel):
    final_intensity: int
    focus_cost: int
    volatility_strike: bool
    volatility_narrative: Optional[str] = None
    resonance_bonus: int
    resonance_narrative: str
    math_log: str
