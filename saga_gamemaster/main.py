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
    
    import random
    ACTIVE_CAMPAIGNS[camp_id] = {
        "player_id": req.player_id,
        "current_hex": req.starting_hex_id,
        "day": 1,
        "player_vitals": {
            "current_hp": 20, "max_hp": 20, 
            "stamina": 12, "max_stamina": 12,
            "composure": 10, "max_composure": 10,
            "focus": 10, "max_focus": 10
        },
        "chaos_level": random.randint(1, 12),
        "active_encounter": None,
        "injuries": []
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
        "vtt_commands": final_state["vtt_commands"],
        "active_encounter": final_state.get("active_encounter")
    }

class TacticalActionRequest(BaseModel):
    campaign_id: str
    skill_name: str
    skill_rank: int
    stat_mod: int
    has_advantage: bool = False
    has_disadvantage: bool = False
    target: dict
    attacker_attributes: dict
    attacker_vitals: dict
    equipped_items: list

@app.post("/api/player/action")
async def process_tactical_action(req: TacticalActionRequest):
    """Bridge between VTT ActionHUD and Port 8007 Clash Engine."""
    from core.api_gateway import SAGA_API_Gateway
    import random
    gateway = SAGA_API_Gateway()
    
    global active_enemies
    if 'active_enemies' not in globals():
        globals()['active_enemies'] = {}
    
    # ── Chaos Check ──
    # User rule: Any risky roll matching Chaos Level triggers a Warp.
    if not ACTIVE_CAMPAIGNS:
         start_chaos = random.randint(1, 12)
         ACTIVE_CAMPAIGNS["CAMPAIGN_001"] = {
             "chaos_level": start_chaos,
             "chaos_history": [start_chaos],
             "injuries": []
         }
         logging.info(f"--- S.A.G.A Campaign Initialized --- Chaos Level: {start_chaos}")

    chaos_triggered = False
    player_roll = random.randint(1, 20)
    # We find the first campaign to get the chaos level (UI currently supports 1 active)
    chaos_level = 1
    current_camp_id = None
    for cid, camp in ACTIVE_CAMPAIGNS.items():
        chaos_level = camp.get("chaos_level", 1)
        current_camp_id = cid
        break
    
    if player_roll == chaos_level:
        chaos_triggered = True
        # Escalate Chaos
        if current_camp_id:
            ACTIVE_CAMPAIGNS[current_camp_id]["chaos_level"] = min(12, chaos_level + 1)
    
    # Extract stats
    player_hp = int(req.attacker_vitals.get("hp", {}).get("current", 20))
    player_stamina = int(req.attacker_vitals.get("stamina", {}).get("current", 12))
    player_focus = int(req.attacker_vitals.get("focus", {}).get("current", 10))
    player_composure = int(req.attacker_vitals.get("composure", {}).get("current", 10))
    
    # ── Dynamic Loadout Resolution ──
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
        "skill_rank": req.skill_rank,
        "stat_mod": req.stat_mod,
        "weapon_damage_dice": weapon_dice, 
        "stamina_burned": stamina_burn,
        "focus_burned": focus_burn
    }
    
    target_id = req.target.get("id", "enemy_unknown")
    camp_id = req.campaign_id
    
    # ── S.A.G.A Rule: Dead is Dead ──
    # Check if the target was already deleted or doesn't exist in the active combat list.
    if target_id not in active_enemies:
        # Check if we can initialize this enemy from the campaign's active encounter
        if camp_id in ACTIVE_CAMPAIGNS:
            camp = ACTIVE_CAMPAIGNS[camp_id]
            enc = camp.get("active_encounter")
            if enc and enc.get("tokens"):
                target_token = next((t for t in enc["tokens"] if t["id"] == target_id), None)
                if target_token:
                    print(f"[GM] Initializing enemy {target_id} from Active Encounter data.")
                    active_enemies[target_id] = {
                        "id": target_id,
                        "name": target_token.get("name", "Unknown"),
                        "current_hp": target_token.get("current_hp", 15),
                        "attack_or_defense_pool": target_token.get("attack_or_defense_pool", 4),
                        "weapon_dice": target_token.get("weapon_dice", "1d6")
                    }
        
    if target_id not in active_enemies:
        return {
            "resolution_text": "ENCOUNTER OVER: The target is no longer present.",
            "vitals_update": req.attacker_vitals,
            "new_target_hp": 0,
            "encounter_ended": True
        }
        
    defender_data = {
        "name": req.target.get("name", "Unknown Enemy"),
        "current_hp": active_enemies[target_id]["hp"],
        "skill_rank": 2, # NPC baseline
        "stat_mod": 2,
        "weapon_damage_dice": "1d6",
        "stamina_burned": 0,
        "focus_burned": 0
    }
    
    clash_result = await gateway.resolve_clash(
        attacker_data=attacker_data,
        defender_data=defender_data,
        chaos_level=chaos_level,
        attacker_adv=req.has_advantage,
        attacker_dis=req.has_disadvantage
    )
    
    # ... (Tie-breaker logic remains) ...
    if clash_result.get("clash_result") == "CLASH_TIE":
        atk_tie = random.randint(1, 20) + req.skill_rank
        def_tie = random.randint(1, 20) + 2
        if atk_tie > def_tie:
            clash_result["resolution_extra"] = "TIE BROKEN: Player force win!"
            clash_result["defender_hp_change"] = -2
        elif def_tie > atk_tie:
            clash_result["resolution_extra"] = "TIE BROKEN: Enemy outlasts you!"
            clash_result["attacker_hp_change"] = -2
        else:
            clash_result["resolution_extra"] = "DEADLOCK CONTINUES."

    # Update state
    dmg_dealt = clash_result.get("defender_hp_change", 0)
    active_enemies[target_id]["hp"] = max(0, active_enemies[target_id]["hp"] + dmg_dealt)
    
    stress_dealt = clash_result.get("defender_composure_change", 0)
    active_enemies[target_id]["composure"] = max(0, active_enemies[target_id]["composure"] + stress_dealt)
    
    player_dmg = clash_result.get("attacker_hp_change", 0)
    final_player_hp = max(0, player_hp + player_dmg)
    
    player_stress = clash_result.get("attacker_composure_change", 0)
    final_player_composure = max(0, player_composure + player_stress)
    
    is_defeated = active_enemies[target_id]["hp"] <= 0 or active_enemies[target_id]["composure"] <= 0
    
    # VTT updates
    updated_vitals = req.attacker_vitals.copy()
    if "stamina" in updated_vitals: updated_vitals["stamina"]["current"] = new_stamina
    if "hp" in updated_vitals: updated_vitals["hp"]["current"] = final_player_hp
    if "focus" in updated_vitals: updated_vitals["focus"]["current"] = new_focus
    if "composure" in updated_vitals: updated_vitals["composure"]["current"] = final_player_composure
        
    status_msg = f"ROLL: {player_roll} vs Chaos {chaos_level}. Result: {clash_result['clash_result']}."
    if chaos_triggered:
        status_msg += " !! CHAOS WARP TRIGGERED !!"
    
    status_msg += f" Margin: {clash_result['margin']}. Dmg/Stress: {dmg_dealt}/{stress_dealt}."
    
    # (Injury Escalation logic remains)
    if clash_result.get("defender_injury_applied") and current_camp_id:
        new_injury = clash_result["defender_injury_applied"]
        camp = ACTIVE_CAMPAIGNS[current_camp_id]
        camp["injuries"].append(new_injury)
        minors = [i for i in camp["injuries"] if "MINOR" in i]
        majors = [i for i in camp["injuries"] if "MAJOR" in i]
        if len(minors) >= 2:
            status_msg += " (2 Minors converted to 1 MAJOR!)"
            camp["injuries"] = [i for i in camp["injuries"] if "MINOR" not in i]
            camp["injuries"].append("MAJOR: Injury Escalation (2 Minors)")
        if len(majors) >= 3:
             is_defeated = True # KO
             status_msg += " !! OVER-INJURED: KNOCKOUT !!"

    if is_defeated:
        status_msg += " Target defeated!"
        del active_enemies[target_id]
        if current_camp_id:
            ACTIVE_CAMPAIGNS[current_camp_id]["active_encounter"] = None
    
    return {
        "resolution_text": status_msg + f" {clash_result.get('resolution_extra', '')}",
        "vitals_update": updated_vitals,
        "new_target_hp": 0 if is_defeated else active_enemies[target_id]["hp"],
        "encounter_ended": is_defeated
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
