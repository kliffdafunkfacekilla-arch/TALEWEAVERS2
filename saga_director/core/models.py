from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class CampaignState(Base):
    __tablename__ = 'campaign_states'
    
    id = Column(String, primary_key=True, index=True) # E.g., "CAMP_001"
    player_id = Column(String)
    current_hex = Column(Integer, default=402)
    day = Column(Integer, default=1)
    chaos_level = Column(Integer, default=1)
    
    # World state
    tension = Column(Integer, default=0)
    weather = Column(String, default="Clear Skies")
    chaos_numbers = Column(JSON, default=[]) # New: Active chaos strike targets (d12)
    pacing_current = Column(Integer, default=0)
    pacing_goal = Column(Integer, default=2)
    
    # Complex blobs
    player_vitals = Column(JSON, default={})
    active_encounter = Column(JSON, nullable=True)
    active_enemies = Column(JSON, default={}) # Persistent combat tokens
    injuries = Column(JSON, default=[])
    player_sprite = Column(JSON, nullable=True) # Icon/Sprite metadata
    
    # Legacy/Metadata
    calendar_state = Column(JSON, default={"year": 1024, "day": 1})
    world_deltas = Column(JSON, default=[])

class CampaignFrameworkTable(Base):
    __tablename__ = 'campaign_frameworks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String, ForeignKey("campaign_states.id"))
    arc_name = Column(String)
    theme = Column(String)
    hero_journey = Column(JSON) # List of StoryArcStage
    character_hooks = Column(JSON)
    current_stage_index = Column(Integer, default=0)
    current_stage_progress = Column(Integer, default=0) # Tracks side-quests/filler counts

class ChatMessage(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String, ForeignKey("campaign_states.id"))
    role = Column(String) # "user" or "assistant"
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActiveQuest(Base):
    __tablename__ = 'active_quests'
    
    id = Column(String, primary_key=True, index=True)
    campaign_id = Column(String, ForeignKey("campaign_states.id"))
    parent_id = Column(String, nullable=True) # Link to Saga beat or Arc
    tier = Column(String, default="SIDE_QUEST")
    title = Column(String)
    giver_faction = Column(String)
    
    # E.g., [{"objective": "Find the cave", "is_complete": False, "target_hex": "[10, 15]", "target_node_id": "POI_1"}]
    objectives = Column(JSON, default=[])
