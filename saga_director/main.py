from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.ai_narrator.graph import create_director_graph
from core.ai_narrator.state import GameState
from core.models import Base, CampaignState, ChatMessage, ActiveQuest, CampaignFrameworkTable, WorldEventsLog
from sqlalchemy.orm import Session
import uuid
import json
import os
import random
import httpx
from core.api_gateway import SAGA_API_Gateway
from core.context import ContextAssembler
from core.tactical_generator import TacticalGenerator
from core.database import SessionLocal, engine

api_gateway = SAGA_API_Gateway()
app = FastAPI(title="Saga Director", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
director_graph = create_director_graph()

class StartCampaignRequest(BaseModel):
    player_id: str
    starting_hex_id: int = 1
    world_id: str = "W_001"
    player_sprite: Optional[dict] = None
    party_size: str = "SOLO"
    difficulty: str = "STANDARD"
    style: str = "GRITTY_SURVIVAL"
    length: str = "SAGA"
    no_fly_list: List[str] = []

@app.post("/api/campaign/start")
async def start_campaign(request: StartCampaignRequest):
    db = SessionLocal()
    campaign_id = str(uuid.uuid4())
    
    pacing_goal_map = {"ONE_SHOT": 5, "SAGA": 15, "EPIC": 999}
    
    new_campaign = CampaignState(
        id=campaign_id,
        player_id=request.player_id,
        current_hex=request.starting_hex_id,
        tension=10,
        weather="Clear Skies",
        chaos_numbers=json.dumps([random.randint(1, 12)]),
        pacing_current=0,
        pacing_goal=pacing_goal_map.get(request.length, 15),
        player_sprite=request.player_sprite,
        difficulty=request.difficulty,
        style=request.style,
        length_type=request.length,
        no_fly_list=json.dumps(request.no_fly_list)
    )
    db.add(new_campaign)
    
    # ── SAGA GENERATION (SESSION ZERO) ──
    weaver_request = {
        "characters": [request.player_sprite] if request.player_sprite else [{"name": "Lone Traveler"}],
        "world_state": {"world_id": request.world_id, "starting_hex": request.starting_hex_id},
        "settings": {
            "difficulty": request.difficulty,
            "style": request.style,
            "length": request.length,
            "no_fly_list": request.no_fly_list
        },
        "history": []
    }
    
    framework_data = await api_gateway.generate_campaign_framework(weaver_request)
    if framework_data:
        hero_journey = framework_data.get("hero_journey", [])
        db_framework = CampaignFrameworkTable(
            campaign_id=campaign_id,
            arc_name=framework_data.get("arc_name", "A Bound Destiny"),
            theme=framework_data.get("theme", request.style),
            hero_journey=hero_journey,
            character_hooks=framework_data.get("character_hooks", [])
        )
        db.add(db_framework)
        
        # ── INITIAL LANDING (SESSION ONE) ──
        assembler = ContextAssembler()
        context = await assembler.assemble(campaign_id, request.starting_hex_id, "MORNING", 0)
        
        biome = context["location"]["biome"]
        initial_encounter = TacticalGenerator.generate_ambient_encounter(biome, request.starting_hex_id, context["active_npcs"])
        new_campaign.active_encounter = initial_encounter

        if hero_journey:
            first_beat = hero_journey[0]
            new_quest = ActiveQuest(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                title=first_beat.get("title", "Call to Adventure"),
                objectives=[{"objective": first_beat.get("narrative_objective", ""), "is_complete": False}]
            )
            db.add(new_quest)

    db.commit()
    
    # Generate Arrival Narration via Graph
    arrival_input = {
        "campaign_id": campaign_id,
        "player_id": request.player_id,
        "player_input": "INITIAL_LANDING" 
    }
    
    # We pass the db session to avoid closing it prematurely
    arrival_response = await process_chat_action_internal(arrival_input, db)
    db.close()
    
    return {
        "campaign_id": campaign_id, 
        "start_hex": request.starting_hex_id,
        "narration": arrival_response.get("narration"),
        "active_encounter": arrival_response.get("active_encounter"),
        "initial_state": arrival_response
    }

async def process_chat_action_internal(data: dict, db: Session):
    campaign_id = data.get("campaign_id")
    player_id = data.get("player_id")
    player_input = data.get("player_input")
    
    campaign = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
    if not campaign:
        return {"error": "Campaign not found"}

    framework_record = db.query(CampaignFrameworkTable).filter(CampaignFrameworkTable.campaign_id == campaign_id).first()
    active_framework = framework_record.hero_journey if framework_record and framework_record.hero_journey else []

    initial_state: GameState = {
        "player_id": player_id,
        "action_type": "MOVE" if "move" in player_input.lower() else "STUNT" if "stunt" in player_input.lower() else "CHAT" if player_input != "INITIAL_LANDING" else "LANDING",
        "action_target": player_input.split("to")[-1].strip() if "move" in player_input.lower() else "",
        "raw_chat_text": player_input if player_input != "INITIAL_LANDING" else "I have arrived.",
        "stamina_burned": 0,
        "focus_burned": 0,
        "current_location": str(campaign.current_hex),
        "player_vitals": {},
        "player_powers": [],
        "active_quests": [],
        "weather": campaign.weather,
        "tension": campaign.tension,
        "chaos_numbers": json.loads(str(campaign.chaos_numbers)),
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
        "campaign_framework": active_framework,
        "current_stage": 0,
        "current_stage_progress": campaign.pacing_current,
        "active_regional_arcs": [],
        "active_local_quests": [],
        "active_errands": [],
        "ai_narration": "",
        "chat_history": [],
        "player_sprite": campaign.player_sprite,
        "difficulty": campaign.difficulty,
        "style": campaign.style,
        "length_type": campaign.length_type,
        "no_fly_list": json.loads(str(campaign.no_fly_list)) if campaign.no_fly_list else [],
        "pacing_goal": campaign.pacing_goal,
        "active_encounter": campaign.active_encounter
    }

    final_output = await director_graph.ainvoke(initial_state)

    campaign.current_hex = int(final_output["current_location"])
    campaign.tension = final_output["tension"]
    campaign.weather = final_output.get("weather", campaign.weather)
    campaign.chaos_numbers = json.dumps(final_output["chaos_numbers"])
    campaign.active_encounter = final_output.get("active_encounter")
    
    stage_advanced = final_output.get("current_stage", 0) > initial_state.get("current_stage", 0)
    progress_advanced = final_output.get("current_stage_progress", 0) > initial_state.get("current_stage_progress", 0)
    
    if stage_advanced or progress_advanced:
        reason = "A new Saga Stage began." if stage_advanced else "A local objective was accomplished."
        narration = final_output.get("ai_narration", "")
        event_desc = f"{reason} Outcome: {narration[:150]}..."
        log_entry = WorldEventsLog(
            campaign_id=campaign_id,
            turn_number=len(final_output.get("chat_history", [])) + 1,
            event_description=event_desc,
            location_hex_id=str(campaign.current_hex)
        )
        db.add(log_entry)

    campaign.pacing_current = final_output.get("current_stage_progress", campaign.pacing_current)

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
        "player_sprite": final_output.get("player_sprite"),
        "active_encounter": campaign.active_encounter
    }
    return response

@app.post("/api/campaign/action")
async def process_chat_action(request: Request):
    data = await request.json()
    db = SessionLocal()
    response = await process_chat_action_internal(data, db)
    db.commit()
    db.close()
    return response

@app.post("/api/world/pulse_simulation/")
async def pulse_simulation(payload: dict):
    campaign_id = payload.get("campaign_id")
    if not campaign_id: return {"error": "Missing campaign_id"}
    architect_url = os.getenv("WORLD_ARCHITECT_URL", "http://localhost:8002")
    db = SessionLocal()
    logs = db.query(WorldEventsLog).filter(WorldEventsLog.campaign_id == campaign_id).all()
    events_export = [{"campaign_id": log.campaign_id, "turn_number": log.turn_number, "event_description": log.event_description, "associated_faction": log.associated_faction, "location_hex_id": log.location_hex_id} for log in logs]
    db.close()
    async with httpx.AsyncClient(timeout=60.0) as client:
        await client.post(f"{architect_url}/api/world/inject_events", json={"campaign_id": campaign_id, "events": events_export})
        tick_resp = await client.post(f"{architect_url}/api/world/tick", json={"campaign_id": campaign_id, "ticks": 5})
        tick_data = tick_resp.json()
    return {"status": "success", "message": f"World advanced 5 ticks. Year {tick_data.get('year')}, {tick_data.get('season')}.", "faction_summary": tick_data.get("factions", [])}

@app.get("/api/campaign/load/{campaign_id}")
async def load_campaign(campaign_id: str):
    db = SessionLocal()
    campaign = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
    db.close()
    if campaign:
        return {"current_hex": campaign.current_hex, "tension": campaign.tension, "weather": campaign.weather, "chaos_numbers": json.loads(campaign.chaos_numbers), "pacing": {"current": campaign.pacing_current, "goal": campaign.pacing_goal}, "active_encounter": campaign.active_encounter}
    return {"error": "NotFound"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

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

    # Fetch Campaign Framework
    framework_record = db.query(CampaignFrameworkTable).filter(CampaignFrameworkTable.campaign_id == campaign_id).first()
    active_framework = framework_record.hero_journey if framework_record and framework_record.hero_journey else []

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
        "chaos_numbers": json.loads(str(campaign.chaos_numbers)),
        "math_log": "",
        "chaos_strike": False,
        "chaos_narrative": "",
        "visual_assets": {
            "forest": f"{os.getenv('ASSET_FOUNDRY_URL', 'http://localhost:8012')}/public/floor/grass_full_new.png",
            "ruins": f"{os.getenv('ASSET_FOUNDRY_URL', 'http://localhost:8012')}/public/tiles/floor_stone.png",
            "mountain": f"{os.getenv('ASSET_FOUNDRY_URL', 'http://localhost:8012')}/public/floor/floor_sand_rock_0.png",
            "swamp": f"{os.getenv('ASSET_FOUNDRY_URL', 'http://localhost:8012')}/public/floor/swamp_0_new.png",
            "tundra": f"{os.getenv('ASSET_FOUNDRY_URL', 'http://localhost:8012')}/public/floor/ice_0_new.png"
        },
        "director_override": None,
        "vtt_commands": [],
        "campaign_framework": active_framework,
        "current_stage": 0,
        "current_stage_progress": campaign.pacing_current,
        "active_regional_arcs": [],
        "active_local_quests": [],
        "active_errands": [],
        "ai_narration": "",
        "chat_history": [],
        "player_sprite": campaign.player_sprite,
        "difficulty": campaign.difficulty,
        "style": campaign.style,
        "length_type": campaign.length_type,
        "no_fly_list": json.loads(str(campaign.no_fly_list)) if campaign.no_fly_list else [],
        "pacing_goal": campaign.pacing_goal
    }

    # Run Director Graph
    final_output = await director_graph.ainvoke(initial_state)

    # Persist Changes
    campaign.current_hex = int(final_output["current_location"])
    campaign.tension = final_output["tension"]
    campaign.weather = final_output.get("weather", campaign.weather)
    campaign.chaos_numbers = json.dumps(final_output["chaos_numbers"])
    
    # Check for Narrative Shift & Log into Chronicle Ledger
    stage_advanced = final_output.get("current_stage", 0) > initial_state.get("current_stage", 0)
    progress_advanced = final_output.get("current_stage_progress", 0) > initial_state.get("current_stage_progress", 0)
    
    if stage_advanced or progress_advanced:
        reason = "A new Saga Stage began." if stage_advanced else "A local objective was accomplished."
        narration = final_output.get("ai_narration", "")
        # Very simple synthesis: "Player accomplished X: [Narration Snippet]"
        event_desc = f"{reason} Outcome: {narration[:150]}..."
        
        log_entry = WorldEventsLog(
            campaign_id=campaign_id,
            turn_number=len(final_output.get("chat_history", [])) + 1,
            event_description=event_desc,
            associated_faction=None, # To be fleshed out by deeper AI parsing if needed
            location_hex_id=str(campaign.current_hex)
        )
        db.add(log_entry)

    campaign.pacing_current = final_output.get("current_stage_progress", campaign.pacing_current)

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

@app.post("/api/world/pulse_simulation/")
async def pulse_simulation(payload: dict):
    campaign_id = payload.get("campaign_id")
    if not campaign_id:
        return {"error": "Missing campaign_id"}

    architect_url = os.getenv("WORLD_ARCHITECT_URL", "http://localhost:8002")

    # 1. Export the WorldEventsLog for this campaign
    db = SessionLocal()
    logs = db.query(WorldEventsLog).filter(WorldEventsLog.campaign_id == campaign_id).all()
    events_export = [
        {
            "campaign_id": log.campaign_id,
            "turn_number": log.turn_number,
            "event_description": log.event_description,
            "associated_faction": log.associated_faction,
            "location_hex_id": log.location_hex_id
        }
        for log in logs
    ]
    db.close()

    import httpx
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 2. Send events to the Python World Simulator
        print(f"[DIRECTOR] Injecting {len(events_export)} chronicle events into Saga Architect...")
        inject_resp = await client.post(
            f"{architect_url}/api/world/inject_events",
            json={"campaign_id": campaign_id, "events": events_export}
        )
        if inject_resp.status_code != 200:
            return {"error": "Saga Architect failed to accept events", "details": inject_resp.text}

        # 3. Advance the world simulation by 5 ticks
        print("[DIRECTOR] Pulsing world simulation 5 ticks...")
        tick_resp = await client.post(
            f"{architect_url}/api/world/tick",
            json={"campaign_id": campaign_id, "ticks": 5}
        )
        if tick_resp.status_code != 200:
            return {"error": "Saga Architect tick failed", "details": tick_resp.text}

        tick_data = tick_resp.json()

    print(f"[DIRECTOR] World pulsed. Now Year {tick_data.get('year')}, Season: {tick_data.get('season')}")
    return {
        "status": "success",
        "message": f"World advanced 5 ticks. Year {tick_data.get('year')}, {tick_data.get('season')}.",
        "faction_summary": tick_data.get("factions", [])
    }

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
