from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import uuid

class NarrativeTier(str, Enum):
    SAGA = "SAGA"             # Tier 1: 8-beat Hero's Journey (Global)
    ARC = "ARC"               # Tier 2/3: Regional bridge between Saga beats
    SIDE_QUEST = "SIDE_QUEST" # Tier 4: Local hex-based tasks
    ERRAND = "ERRAND"         # Tier 5: Tactical/Daily one-offs

class QuestNode(BaseModel):
    id: str = Field(default_factory=lambda: f"Q_{uuid.uuid4().hex[:6].upper()}")
    tier: NarrativeTier = Field(default=NarrativeTier.SIDE_QUEST)
    parent_id: Optional[str] = None
    step_number: int = Field(..., description="The sequence order of this quest step")
    narrative_objective: str = Field(..., description="E.g., 'Find the Wolf Cult's hideout.'")
    trigger_location: str = Field(..., description="The exact hex ID or Settlement ID from Module 2")
    target_node_id: Optional[str] = Field(None, description="The specific Tier 4 node ID (POI) associated with this objective")
    encounter_type: str = Field(..., description="'SOCIAL', 'HAZARD', 'COMBAT' (Fed to Module 4)")
    description: Optional[str] = Field(None, description="Detailed description")
    target_entity: Optional[str] = Field(None, description="Who or what is the primary focus of this node? (e.g., 'Kaelen, Rogue Pyromancer' or 'Starving Wolf Pack')")
    employer_or_faction: Optional[str] = Field(None, description="Who issued this quest or who benefits from it? (e.g., 'The Ashen Dawn' or 'Local Militia')")
    local_impact_description: Optional[str] = Field(None, description="Why does this matter to the local region? What is the impact?")
    success_state_change: str = Field(..., description="E.g., 'UNLOCK_STEP_2'")
    sub_tasks: List["QuestNode"] = Field(default_factory=list)

class CampaignRoadmap(BaseModel):
    campaign_name: str = Field(..., description="The procedural name of the campaign")
    main_antagonist_faction: str = Field(..., description="The faction driving the conflict")
    starting_location: str = Field(..., description="Where the players begin their journey")
    quest_nodes: List[QuestNode] = Field(..., description="The sequential steps of the campaign")

class StoryArcStage(BaseModel):
    id: str = Field(default_factory=lambda: f"SAGA_{uuid.uuid4().hex[:4].upper()}")
    tier: NarrativeTier = Field(default=NarrativeTier.SAGA)
    stage_name: str = Field(..., description="E.g., 'The Call to Adventure'")
    plot_point: str = Field(..., description="The core narrative event of this stage")
    narrative_objective: str = Field(..., description="What the player needs to accomplish")
    foreshadowing_clue: str = Field(..., description="A hint or secret to be revealed early in the game")
    pacing_milestones: int = Field(default=2, description="Number of side-quests or discovery events required before this stage can conclude")
    sub_arcs: List[QuestNode] = Field(default_factory=list) # Tier 2 ARCs

class CampaignFramework(BaseModel):
    arc_name: str = Field(..., description="The procedural name of the long-term story arc")
    theme: str = Field(..., description="The overall narrative theme")
    hero_journey: List[StoryArcStage] = Field(..., description="The 8 stages of the Hero's Journey arc")
    character_hooks: List[str] = Field(..., description="Specific ties to player backstories")

QuestNode.model_rebuild()
