from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CampaignState(Base):
    __tablename__ = 'campaign_states'
    
    id = Column(String, primary_key=True, index=True) # E.g., "CAMP_001"
    current_node_name = Column(String, default="Starting Town")
    chaos_level = Column(Integer, default=1)
    
    # Store the exact time/date of the world
    calendar_state = Column(JSON, default={"year": 1024, "day": 1})
    
    # Store World Deltas (e.g., Faction X took over Settlement Y)
    world_deltas = Column(JSON, default=[])

class ActiveQuest(Base):
    __tablename__ = 'active_quests'
    
    id = Column(String, primary_key=True, index=True)
    campaign_id = Column(String, ForeignKey("campaign_states.id"))
    title = Column(String)
    giver_faction = Column(String)
    
    # E.g., [{"objective": "Find the cave", "is_complete": False, "target_hex": "[10, 15]"}]
    objectives = Column(JSON, default=[])
