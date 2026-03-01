from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from core.vtt_schemas import PlayerAction, VTTUpdate
from core.database import get_session, init_db
from core.models import CampaignState, ChatMessage, CampaignFrameworkTable
from core.ai_narrator.graph import create_director_graph
from core.ai_narrator.state import GameState
from core.api_gateway import SAGA_API_Gateway
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import uuid
import datetime
import json
import os

app = FastAPI(title="SAGA Core GM App")

@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "Core Game Master", "port": 8000}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

director_graph = create_director_graph()
api_gateway = SAGA_API_Gateway()

@app.on_event("startup")
async def startup_event():
    await init_db()

class StartCampaignRequest(BaseModel):
    world_id: str
    starting_hex_id: int
    player_id: str

class PlayerChatRequest(BaseModel):
    campaign_id: str
    player_input: str

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

@app.post("/api/campaign/start")
async def start_campaign(req: StartCampaignRequest, db: AsyncSession = Depends(get_session)):
    camp_id = f"CAMP_{uuid.uuid4().hex[:8].upper()}"
    char_data = await api_gateway.get_character(req.player_id)
    vitals = char_data["survival_pools"] if char_data else {"current_hp": 20, "max_hp": 20, "stamina": 12, "max_stamina": 12, "composure": 10, "max_composure": 10, "focus": 10, "max_focus": 10}
    
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")
    world_state = {}
    if os.path.exists(MAP_FILE):
        with open(MAP_FILE, "r") as f: world_state = json.load(f)
            
    framework_data = await api_gateway.generate_framework(
        characters=[char_data or {"name": req.player_id}],
        world_state=world_state,
        settings={"difficulty": "STANDARD", "theme": "GRIMDARK"}
    )
    
    import random
    new_campaign = CampaignState(id=camp_id, player_id=req.player_id, current_hex=req.starting_hex_id, day=1, player_vitals=vitals, chaos_level=random.randint(1, 12))
    db.add(new_campaign)
    
    if framework_data:
        new_framework = CampaignFrameworkTable(
            campaign_id=camp_id,
            arc_name=framework_data["arc_name"],
            theme=framework_data["theme"],
            hero_journey=framework_data["hero_journey"],
            character_hooks=framework_data["character_hooks"],
            current_stage_index=0
        )
        db.add(new_framework)
    
    await db.commit()
    return {"campaign_id": camp_id, "status": "Hero's Journey Arc Initialized."}

@app.post("/api/campaign/action")
async def process_chat_action(req: PlayerChatRequest, db: AsyncSession = Depends(get_session)):
    q = await db.execute(select(CampaignState).where(CampaignState.id == req.campaign_id))
    state = q.scalar_one_or_none()
    if not state: raise HTTPException(status_code=404, detail="Campaign not found.")
    
    fq = await db.execute(select(CampaignFrameworkTable).where(CampaignFrameworkTable.campaign_id == req.campaign_id))
    framework_row = fq.scalar_one_or_none()
    
    hq = await db.execute(select(ChatMessage).where(ChatMessage.campaign_id == req.campaign_id).order_by(ChatMessage.created_at.desc()).limit(10))
    history_objs = hq.scalars().all()
    history = [{"role": h.role, "content": h.content} for h in reversed(history_objs)]
    
    initial_state: GameState = {
        "player_id": state.player_id,
        "action_type": "GENERAL",
        "action_target": str(state.current_hex),
        "raw_chat_text": req.player_input,
        "stamina_burned": 0,
        "current_location": "Unknown",
        "active_quests": [],
        "player_vitals": state.player_vitals,
        "math_log": "",
        "director_override": None,
        "vtt_commands": [],
        "active_encounter": state.active_encounter,
        "ai_narration": "",
        "chat_history": history,
        "campaign_framework": framework_row.hero_journey if framework_row else None,
        "current_stage": framework_row.current_stage_index if framework_row else 0,
        "current_stage_progress": framework_row.current_stage_progress if framework_row else 0
    }
    
    final_state = await director_graph.ainvoke(initial_state)
    
    db.add(ChatMessage(campaign_id=req.campaign_id, role="user", content=req.player_input))
    db.add(ChatMessage(campaign_id=req.campaign_id, role="assistant", content=final_state["ai_narration"]))
    
    state.player_vitals = final_state["player_vitals"]
    state.active_encounter = final_state.get("active_encounter")
    
    # ── Narrative Sync ──
    if framework_row:
        if "campaign_framework" in final_state and final_state["campaign_framework"] != framework_row.hero_journey:
            framework_row.hero_journey = final_state["campaign_framework"]
            print("[SYNC] Framework Patched.")
        if "current_stage" in final_state and final_state["current_stage"] != framework_row.current_stage_index:
            framework_row.current_stage_index = final_state["current_stage"]
            framework_row.current_stage_progress = 0 # Reset progress on stage advance
            print(f"[SYNC] Stage Advanced to {final_state['current_stage']}.")
        elif "current_stage_progress" in final_state:
            framework_row.current_stage_progress = final_state["current_stage_progress"]
            
        # ── Nested Hierarchy Sync ──
        if "active_regional_arcs" in final_state:
            framework_row.character_hooks = final_state["active_regional_arcs"] # Repurposing hooks/metadata columns or we should add new ones
            # For now, let's just use the hero_journey blob to store transient state or add a dedicated column
            # Given the schema, I'll store the nested state in the JSON blobs.
        
        # Actually, let's update the framework row properly. 
        # I'll save the updated progress and indices.
            
    await db.commit()
    return {"narration": final_state["ai_narration"], "updated_vitals": final_state["player_vitals"], "current_hex": state.current_hex}

@app.get("/api/campaign/load/{campaign_id}")
async def load_campaign(campaign_id: str, db: AsyncSession = Depends(get_session)):
    q = await db.execute(select(CampaignState).where(CampaignState.id == campaign_id))
    state = q.scalar_one_or_none()
    if not state: raise HTTPException(status_code=404, detail="Campaign not found.")
    return {"state": {"id": state.id, "current_hex": state.current_hex, "vitals": state.player_vitals}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
