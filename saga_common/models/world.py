from pydantic import BaseModel
from typing import List, Dict, Optional

class CalendarState(BaseModel):
    year: int = 1024
    day: int = 1
    era: str = "Age of Awakening"

class WorldDelta(BaseModel):
    event_type: str
    target_id: str
    description: str
    impact_json: Dict = {}
