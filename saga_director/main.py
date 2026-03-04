from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.ai_narrator.graph import create_director_graph
from core.ai_narrator.state import GameState
from core.models import Base, CampaignState, ChatMessage, ActiveQuest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import uuid
import json
import os
import random

app = FastAPI(title="Saga Director", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./saga_campaigns.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

director_graph = create_director_graph()

class StartCampaignRequest(BaseModel):
    player_id: str
    starting_hex_id: int = 1
    world_id: str = "W_001"
    player_sprite: Optional[dict] = None

@app.post("/api/campaign/start")
async def start_campaign(request: StartCampaignRequest):
    db = SessionLocal()
    campaign_id = str(uuid.uuid4())
    
    new_campaign = CampaignState(
        id=campaign_id,
        player_id=request.player_id,
        current_hex=request.starting_hex_id,
        tension=10,
        weather="Clear Skies",
        chaos_numbers=json.dumps([random.randint(1, 12)]),
        pacing_current=0,
        pacing_goal=2,
        player_sprite=request.player_sprite
    )
    db.add(new_campaign)
    db.commit()
    db.close()
    return {"campaign_id": campaign_id, "start_hex": request.starting_hex_id}

@app.post("/api/campaign/action")
async def process_chat_action(request: Request):
    data = await request.json()
    campaign_id = data.get("campaign_id")
    player_id = data.get("player_id")
    player_input = data.get("player_input")
    
    db = SessionLocal()
    campaign = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
    if not campaign:
        db.close()
        return {"error": "Campaign not found"}

    # Sync state for Graph
    initial_state: GameState = {
        "player_id": player_id,
        "action_type": "MOVE" if "move" in player_input.lower() else "STUNT" if "stunt" in player_input.lower() else "CHAT",
        "action_target": player_input.split("to")[-1].strip() if "move" in player_input.lower() else "",
        "raw_chat_text": player_input,
        "stamina_burned": 0,
        "focus_burned": 0,
        "current_location": str(campaign.current_hex),
        "player_vitals": {},
        "player_powers": [],
        "active_quests": [],
        "weather": campaign.weather,
        "tension": campaign.tension,
        "chaos_numbers": json.loads(campaign.chaos_numbers),
        "math_log": "",
        "chaos_strike": False,
        "chaos_narrative": "",
        "visual_assets": {
            "forest": "http://localhost:8012/public/floor/grass_full_new.png",
            "ruins": "http://localhost:8012/public/tiles/floor_stone.png",
            "mountain": "http://localhost:8012/public/floor/floor_sand_rock_0.png",
            "swamp": "http://localhost:8012/public/floor/swamp_0_new.png",
            "tundra": "http://localhost:8012/public/floor/ice_0_new.png"
        },
        "director_override": None,
        "vtt_commands": [],
        "campaign_framework": [],
        "current_stage": 0,
        "current_stage_progress": campaign.pacing_current,
        "active_regional_arcs": [],
        "active_local_quests": [],
        "active_errands": [],
        "ai_narration": "",
        "chat_history": [],
        "player_sprite": campaign.player_sprite # Pass sprite to graph
    }

    # Run Director Graph
    final_output = await director_graph.ainvoke(initial_state)

    # Persist Changes
    campaign.current_hex = int(final_output["current_location"])
    campaign.tension = final_output["tension"]
    campaign.weather = final_output.get("weather", campaign.weather)
    campaign.chaos_numbers = json.dumps(final_output["chaos_numbers"])
    campaign.pacing_current = final_output["current_stage_progress"]
    db.commit()

    # Prepare response including visual assets
    response = {
        "narration": final_output["ai_narration"],
        "math_log": final_output["math_log"],
        "updated_vitals": final_output["player_vitals"],
        "current_hex": campaign.current_hex,
        "weather": campaign.weather,
        "tension": campaign.tension,
        "chaos_numbers": final_output["chaos_numbers"],
        "pacing": {"current": campaign.pacing_current, "goal": campaign.pacing_goal},
        "vtt_commands": final_output["vtt_commands"],
        "visual_assets": final_output.get("visual_assets", {}),
        "player_sprite": final_output.get("player_sprite")
    }
    
    db.close()
    return response

@app.get("/api/campaign/load/{campaign_id}")
async def load_campaign(campaign_id: str):
    db = SessionLocal()
    campaign = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
    db.close()
    if campaign:
        return {
            "current_hex": campaign.current_hex,
            "tension": campaign.tension,
            "weather": campaign.weather,
            "chaos_numbers": json.loads(campaign.chaos_numbers),
            "pacing": {"current": campaign.pacing_current, "goal": campaign.pacing_goal}
        }
    return {"error": "NotFound"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
