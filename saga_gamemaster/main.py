from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.vtt_schemas import PlayerAction, VTTUpdate
from core.database import get_session, init_db
from core.ai_narrator.graph import create_director_graph
from core.ai_narrator.state import GameState
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import uuid

app = FastAPI(title="SAGA Core GM App")

@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "Core Game Master", "port": 8000}

# Allow React (Port 5173) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

director_graph = create_director_graph()

# --- IN-MEMORY CAMPAIGN TRACKER ---
# In production, this is persisted via SQLAlchemy (database.py / models.py).
# For rapid prototyping, we keep active sessions in memory for speed.
ACTIVE_CAMPAIGNS = {}

@app.on_event("startup")
async def startup_event():
    await init_db()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXISTING ENDPOINT: Structured VTT Action (used by ActionDeck buttons)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.post("/action", response_model=VTTUpdate)
async def handle_player_action(action: PlayerAction, db: AsyncSession = Depends(get_session)):
    # 1. Initialize State
    initial_state: GameState = {
        "player_id": action.player_id,
        "action_type": action.action_type,
        "action_target": action.action_target,
        "raw_chat_text": action.raw_chat_text,
        "stamina_burned": action.stamina_burned,
        "current_location": "",
        "active_quests": [],
        "player_vitals": {},
        "math_log": "",
        "director_override": None,
        "vtt_commands": [],
        "active_encounter": None,
        "ai_narration": ""
    }
    
    # 2. Run LangGraph Workflow
    try:
        final_state = await director_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 3. Construct VTT Update
    response = VTTUpdate(
        ai_narration_html=f"<div>{final_state['ai_narration']}</div>",
        system_log=final_state["math_log"],
        ui_refresh_required=True if final_state["math_log"] else False,
        vtt_commands=final_state["vtt_commands"],
        active_encounter=final_state.get("active_encounter")
    )
    
    return response

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEW ENDPOINTS: Campaign Management + Text-Based Chat Input
# These enable the "type a sentence" style gameplay from the Director Log
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StartCampaignRequest(BaseModel):
    world_id: str
    starting_hex_id: int
    player_id: str

class PlayerChatRequest(BaseModel):
    campaign_id: str
    player_input: str

@app.post("/api/campaign/start")
async def start_campaign(req: StartCampaignRequest):
    """Drops the player into the world and initializes the session tracker."""
    camp_id = f"CAMP_{uuid.uuid4().hex[:8].upper()}"
    
    ACTIVE_CAMPAIGNS[camp_id] = {
        "player_id": req.player_id,
        "current_hex": req.starting_hex_id,
        "day": 1,
        "player_vitals": {"current_hp": 20, "max_hp": 20, "stamina": 10, "max_stamina": 10},
        "active_encounter": None
    }
    
    print(f"[DIRECTOR] Campaign {camp_id} started at Hex {req.starting_hex_id}.")
    return {"campaign_id": camp_id, "status": "World Initialized. Waiting for player."}

@app.post("/api/campaign/action")
async def process_chat_action(req: PlayerChatRequest):
    """Text-based game loop: receives natural language, routes through LangGraph, returns narrative."""
    if req.campaign_id not in ACTIVE_CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    
    state = ACTIVE_CAMPAIGNS[req.campaign_id]
    
    # Detect intent from the raw text to pick the right action_type
    text_lower = req.player_input.lower()
    if any(word in text_lower for word in ["attack", "strike", "charge", "hit", "slash"]):
        action_type = "ATTACK"
    elif any(word in text_lower for word in ["travel", "walk", "move", "go", "head"]):
        action_type = "TRAVEL"
    elif any(word in text_lower for word in ["use", "drink", "eat", "consume", "apply"]):
        action_type = "USE_ITEM"
    else:
        action_type = "GENERAL"
    
    # Package the state for the LangGraph Engine
    initial_state: GameState = {
        "player_id": state["player_id"],
        "action_type": action_type,
        "action_target": str(state["current_hex"]),
        "raw_chat_text": req.player_input,
        "stamina_burned": 0,
        "current_location": f"Hex #{state['current_hex']}",
        "active_quests": [],
        "player_vitals": state["player_vitals"],
        "math_log": "",
        "director_override": None,
        "vtt_commands": [],
        "active_encounter": state.get("active_encounter"),
        "ai_narration": ""
    }
    
    # Run the exact same LangGraph pipeline as the structured endpoint
    try:
        final_state = await director_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Update campaign tracker with new state
    ACTIVE_CAMPAIGNS[req.campaign_id]["player_vitals"] = final_state["player_vitals"]
    ACTIVE_CAMPAIGNS[req.campaign_id]["active_encounter"] = final_state.get("active_encounter")
    
    return {
        "narration": final_state["ai_narration"],
        "system_log": final_state["math_log"],
        "updated_vitals": final_state["player_vitals"],
        "vtt_commands": final_state["vtt_commands"]
    }

class TacticalActionRequest(BaseModel):
    skill_name: str
    target: dict
    attacker_attributes: dict
    attacker_vitals: dict
    equipped_items: list

@app.post("/api/player/action")
async def process_tactical_action(req: TacticalActionRequest):
    """Bridge between VTT ActionHUD and Port 8007 Clash Engine."""
    from core.api_gateway import SAGA_API_Gateway
    gateway = SAGA_API_Gateway()
    
    global active_enemies
    if 'active_enemies' not in globals():
        globals()['active_enemies'] = {}
    
    # Extract specific stats based on the ActionHUD JSON
    player_pool = int(req.attacker_attributes.get("might", 0)) + int(req.attacker_attributes.get("reflexes", 0))
    player_hp = int(req.attacker_vitals.get("hp", {}).get("current", 20))
    player_stamina = int(req.attacker_vitals.get("stamina", {}).get("current", 12))
    player_focus = int(req.attacker_vitals.get("focus", {}).get("current", 9))
    
    # ── Dynamic Loadout Resolution ──
    # Look for the current weapon in the equipped items
    equipped_weapon = next((item for item in req.equipped_items if item.get("type", "").upper() in ["MELEE", "RANGED", "MAGIC"]), None)
    is_magic = equipped_weapon and equipped_weapon.get("type", "").upper() == "MAGIC"
    
    weapon_dice = equipped_weapon.get("dice", "1d6") if equipped_weapon else "1d4"
    cost = equipped_weapon.get("stamina_cost", 1) if equipped_weapon else 1
    
    focus_burn = cost if is_magic else 0
    stamina_burn = 0 if is_magic else cost
    
    new_stamina = max(0, player_stamina - stamina_burn)
    new_focus = max(0, player_focus - focus_burn)
    
    attacker_data = {
        "name": "Player",
        "current_hp": player_hp,
        "attack_or_defense_pool": player_pool,
        "weapon_damage_dice": weapon_dice, 
        "stamina_burned": stamina_burn,
        "focus_burned": focus_burn
    }
    
    # Stateful Defender Tracking
    target_id = req.target.get("id", "enemy_unknown")
    if target_id not in active_enemies:
        active_enemies[target_id] = 20  # Default Enemy Max HP
        
    defender_data = {
        "name": req.target.get("name", "Unknown Enemy"),
        "current_hp": active_enemies[target_id],
        "attack_or_defense_pool": 8,
        "weapon_damage_dice": "1d6",
        "stamina_burned": 0,
        "focus_burned": 0
    }
    
    clash_result = await gateway.resolve_clash(
        attacker_data=attacker_data,
        defender_data=defender_data
    )
    
    # Apply damage permanently (signed deltas: dmg is negative)
    dmg_dealt = clash_result.get("dmg", 0)
    active_enemies[target_id] = max(0, active_enemies[target_id] + dmg_dealt)
    
    # Counter-attack damage to player if the enemy scored a REVERSAL (signed delta)
    player_dmg_taken = clash_result.get("attacker_dmg", 0)
    final_player_hp = max(0, player_hp + player_dmg_taken)
    
    # Build updated vitals to send back to React
    updated_vitals = req.attacker_vitals.copy()
    if "stamina" in updated_vitals and isinstance(updated_vitals["stamina"], dict):
        updated_vitals["stamina"]["current"] = new_stamina
    if "hp" in updated_vitals and isinstance(updated_vitals["hp"], dict):
        updated_vitals["hp"]["current"] = final_player_hp
    if "focus" in updated_vitals and isinstance(updated_vitals["focus"], dict):
        updated_vitals["focus"]["current"] = new_focus
        
    status_msg = f"Margin: {clash_result['margin']}. Damage dealt: {abs(dmg_dealt)}. Enemy HP: {active_enemies[target_id]}."
    if player_dmg_taken < 0:
        status_msg += f" You took {abs(player_dmg_taken)} counter-damage!"
    is_defeated = active_enemies[target_id] == 0
    if is_defeated:
        status_msg += " Enemy defeated!"
        
        # 1. Clear the enemy from the active tracking pool
        del active_enemies[target_id]
        
        # 2. Clear the encounter in the global campaign state
        for camp in ACTIVE_CAMPAIGNS.values():
            if camp.get("active_encounter"):
                camp["active_encounter"] = None
    
    return {
        "resolution_text": status_msg,
        "vitals_update": updated_vitals,
        "new_target_hp": 0 if is_defeated else active_enemies[target_id],
        "encounter_ended": is_defeated
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
