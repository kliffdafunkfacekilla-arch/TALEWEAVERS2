from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class WorldState(Base):
    """Stores the persisted simulation state of the living world between sessions."""
    __tablename__ = "world_state"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, unique=True, index=True)
    tick_count = Column(Integer, default=0)               # How many sim ticks have run
    year = Column(Integer, default=1)
    season = Column(String, default="SPRING")             # SPRING, SUMMER, AUTUMN, WINTER
    
    # Faction data stored as JSON list of faction dicts
    factions = Column(JSON, default=[])
    
    # Per-hex cell overrides: dict of hex_id -> {population, threat_level, resource_level}
    hex_overrides = Column(JSON, default={})


class FactionRecord(Base):
    """Tracks each live faction's state in the simulation."""
    __tablename__ = "factions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, index=True)
    name = Column(String)
    faction_type = Column(String)         # EMPIRE, TRIBE, CULT, BEAST_PACK, etc.
    military_strength = Column(Float, default=100.0)
    food_supply = Column(Float, default=100.0)
    territory_hex_ids = Column(JSON, default=[])   # List of hex IDs controlled
    at_war_with = Column(JSON, default=[])         # List of faction IDs
    is_expanding = Column(Integer, default=0)      # Boolean flag
    is_starving = Column(Integer, default=0)       # Boolean flag
