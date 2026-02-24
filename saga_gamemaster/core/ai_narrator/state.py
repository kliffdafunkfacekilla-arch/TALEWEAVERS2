from typing import TypedDict, Optional, List, Dict
import operator

class GameState(TypedDict):
    # 1. Input from VTT
    player_id: str
    action_type: str            # e.g., "MOVE", "USE_ITEM", "ATTACK"
    action_target: str          # e.g., "[10, 15]", "ITEM_04", "NPC_99"
    raw_chat_text: Optional[str]
    stamina_burned: int
    
    # 2. Context (Injected automatically)
    current_location: str
    active_quests: List[Dict]
    player_vitals: Dict
    
    # 3. Mechanical Results
    math_log: str               # Output from Math Engines
    
    # 4. The Director's Commands
    director_override: Optional[str] # If populated, LLM must follow this
    vtt_commands: List[str]          # Instructions for React
    
    # 5. Final Output
    ai_narration: str
