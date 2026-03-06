from typing import TypedDict, Optional, List, Dict
import operator

class GameState(TypedDict):
    # 1. Input from VTT
    player_id: str
    action_type: str            # e.g., "MOVE", "USE_ITEM", "ATTACK", "STUNT"
    action_target: str          # e.g., "[10, 15]", "ITEM_04", "NPC_99"
    raw_chat_text: Optional[str]
    stamina_burned: int
    focus_burned: int
    
    # 2. Context (Injected automatically)
    current_location: str
    active_quests: List[Dict]
    player_vitals: Dict
    player_powers: List[Dict]
    weather: str
    tension: int
    chaos_numbers: List[int]
    
    # Living Context Layer
    current_day: int
    current_tick: int
    day_phase: str
    context_packet: Dict
    
    # 3. Mechanical & Tactical Results
    math_log: str               # Output from Math Engines
    chaos_strike: bool
    chaos_narrative: str
    active_encounter: Optional[Dict]
    visual_assets: Dict[str, str] # asset_id -> url
    
    # 4. The Director's Commands
    director_override: Optional[str]
    vtt_commands: List[str]
    
    # 5. Narrative Foresight (Hero's Journey Hierarchy)
    campaign_framework: Optional[List[Dict]]
    current_stage: int
    current_stage_progress: int
    active_regional_arcs: List[Dict]
    active_local_quests: List[Dict]
    active_errands: List[Dict]
    
    # 6. Final Output
    ai_narration: str
    chat_history: List[Dict[str, str]]
    player_sprite: Optional[Dict] # Metadata for the player token
