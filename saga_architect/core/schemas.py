from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class FactionState(BaseModel):
    id: str
    name: str
    faction_type: str                      # EMPIRE, TRIBE, CULT, BEAST_PACK, etc.
    military_strength: float = 100.0
    food_supply: float = 100.0
    territory_hex_ids: List[str] = []
    at_war_with: List[str] = []
    is_expanding: bool = False
    is_starving: bool = False

class HexOverride(BaseModel):
    hex_id: str
    population: Optional[int] = None
    threat_level: Optional[float] = None
    resource_level: Optional[float] = None

class WorldSnapshot(BaseModel):
    campaign_id: str
    tick_count: int
    year: int
    season: str
    factions: List[FactionState]
    hex_overrides: Dict[str, dict] = {}

class InitWorldRequest(BaseModel):
    campaign_id: str
    faction_seeds: List[FactionState] = Field(default=[],
        description="Initial factions to seed the simulation with, parsed from lore files.")
    world_map_path: Optional[str] = Field(None,
        description="Path to the Saga_Master_World.json to hydrate hex data from.")

class TickRequest(BaseModel):
    campaign_id: str
    ticks: int = Field(default=5, ge=1, le=50)

class InjectEventsRequest(BaseModel):
    campaign_id: str
    events: List[dict]   # List of WorldEventsLog-style dicts from saga_director

class ExportResponse(BaseModel):
    campaign_id: str
    world_snapshot: WorldSnapshot
    exported_path: str
