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
    active_encounter: Optional[Dict] # New: The mechanical data for the current threat
    
    # 3. Mechanical Results
    math_log: str               # Output from Math Engines
    
    # 4. The Director's Commands
    director_override: Optional[str] # If populated, LLM must follow this
    vtt_commands: List[str]          # Instructions for React
    
    # 5. Narrative Foresight (Hero's Journey Hierarchy)
    campaign_framework: Optional[List[Dict]] # The 8 SAGA stages
    current_stage: int # Saga Stage Index (0-7)
    current_stage_progress: int # Filler count
    active_regional_arcs: List[Dict] # Tier 2/3 quests bridging saga beats
    active_local_quests: List[Dict] # Tier 4 hex-based sidequests
    active_errands: List[Dict] # Tier 5 tactical one-offs
    
    # 6. Final Output
    ai_narration: str
    chat_history: List[Dict[str, str]] # List of {"role": "user/assistant", "content": "..."}
