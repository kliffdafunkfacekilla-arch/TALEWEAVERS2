from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from saga_gamemaster.core.vtt_schemas import PlayerAction, VTTUpdate
from saga_gamemaster.core.database import get_session, init_db
from saga_gamemaster.core.ai_narrator.graph import create_director_graph
from saga_gamemaster.core.ai_narrator.state import GameState
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import uuid

app = FastAPI(title="SAGA Core GM App", port=8000)

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
        vtt_commands=final_state["vtt_commands"]
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
        "ai_narration": ""
    }
    
    # Run the exact same LangGraph pipeline as the structured endpoint
    try:
        final_state = await director_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Update campaign tracker with new vitals
    ACTIVE_CAMPAIGNS[req.campaign_id]["player_vitals"] = final_state["player_vitals"]
    
    return {
        "narration": final_state["ai_narration"],
        "system_log": final_state["math_log"],
        "updated_vitals": final_state["player_vitals"],
        "vtt_commands": final_state["vtt_commands"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
