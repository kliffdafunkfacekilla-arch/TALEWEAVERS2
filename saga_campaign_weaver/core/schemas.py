from pydantic import BaseModel, Field
from typing import List, Optional

class QuestNode(BaseModel):
    step_number: int = Field(..., description="The sequence order of this quest step")
    narrative_objective: str = Field(..., description="E.g., 'Find the Wolf Cult's hideout.'")
    trigger_location: str = Field(..., description="The exact hex ID or Settlement ID from Module 2")
    encounter_type: str = Field(..., description="'SOCIAL', 'HAZARD', 'COMBAT' (Fed to Module 4)")
    success_state_change: str = Field(..., description="E.g., 'UNLOCK_STEP_2', 'REVEAL_MAP_PIN'")

class CampaignRoadmap(BaseModel):
    campaign_name: str = Field(..., description="The procedural name of the campaign")
    main_antagonist_faction: str = Field(..., description="The faction driving the conflict")
    starting_location: str = Field(..., description="Where the players begin their journey")
    quest_nodes: List[QuestNode] = Field(..., description="The sequential steps of the campaign")
