from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class CampaignStateModel(Base):
    __tablename__ = "campaign_states"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String, unique=True, index=True)
    current_time = Column(JSON)  # {"year": 1024, "season": "Deep Winter", "day": 14}
    party_location_node = Column(String)
    
    quests = relationship("ActiveQuestModel", back_populates="campaign")
    deltas = relationship("WorldDeltaModel", back_populates="campaign")

class ActiveQuestModel(Base):
    __tablename__ = "active_quests"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String, ForeignKey("campaign_states.campaign_id"))
    quest_id = Column(String)
    title = Column(String)
    giver_faction = Column(String)
    is_failed = Column(Boolean, default=False)
    
    campaign = relationship("CampaignStateModel", back_populates="quests")
    objectives = relationship("QuestObjectiveModel", back_populates="quest")

class QuestObjectiveModel(Base):
    __tablename__ = "quest_objectives"
    id = Column(Integer, primary_key=True)
    quest_internal_id = Column(Integer, ForeignKey("active_quests.id"))
    description = Column(String)
    is_complete = Column(Boolean, default=False)
    target_node_id = Column(String, nullable=True)
    
    quest = relationship("ActiveQuestModel", back_populates="objectives")

class WorldDeltaModel(Base):
    __tablename__ = "world_deltas"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String, ForeignKey("campaign_states.campaign_id"))
    node_id = Column(String)
    change_type = Column(String)
    new_value = Column(String)
    
    campaign = relationship("CampaignStateModel", back_populates="deltas")
