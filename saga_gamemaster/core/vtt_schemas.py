from pydantic import BaseModel
from typing import List, Dict, Optional

class PlayerAction(BaseModel):
    player_id: str
    action_type: str            # "ATTACK", "USE_ITEM", "TALK", "TRAVEL", "MOVE"
    action_target: str          # "NPC_Wolf_01", "[10, 15]", "ITEM_04"
    raw_chat_text: Optional[str] = ""
    stamina_burned: int = 0

class VTTUpdate(BaseModel):
    ai_narration_html: str
    system_log: str
    ui_refresh_required: bool
    vtt_commands: List[str] = []
