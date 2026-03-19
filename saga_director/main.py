from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from fastapi.middleware.cors import CORSMiddleware
from core.ai_narrator.graph import create_director_graph
from core.ai_narrator.state import GameState
from core.models import Base, CampaignState, ChatMessage, ActiveQuest, CampaignFrameworkTable, WorldEventsLog
# Simplified phase to hour mapping for NPC schedules
PHASE_HOURS = {
    "DAWN": 6.0,
    "MORNING": 10.0,
    "AFTERNOON": 15.0,
    "EVENING": 19.0,
    "NIGHT": 23.0
}
from sqlalchemy.orm import Session
import uuid
import json
import os
import random
import httpx
from core.api_gateway import SAGA_API_Gateway
from core.context import ContextAssembler
from core.tactical_generator import TacticalGenerator
from core.pathfinder import Pathfinder
from core.world_manager import WorldManager
from core.database import SessionLocal, engine

# Imported from Weaver/Encounter Engines
from core.weaver_schemas import CampaignRoadmap, QuestNode, CampaignFramework
from core.weaver import (
    generate_campaign_framework,
    generate_regional_arc,
    generate_local_sidequest,
    generate_tactical_errand
)
from core.encounter_schemas import EncounterRequest, EncounterResponse
from core.generator import generate_encounter

api_gateway = SAGA_API_Gateway()
# Initialize World Manager with a default seed (can be overridden by campaign)
world_manager = WorldManager(world_seed=918273)
TacticalGenerator.set_world_manager(world_manager)

app = FastAPI(title="Saga Director", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

Base.metadata.create_all(bind=engine)
director_graph = create_director_graph()

class StartCampaignRequest(BaseModel):
    player_id: str
    starting_hex_id: int = 1
    world_id: str = "W_001"
    composite_sprite: Optional[dict] = None
    party_size: str = "SOLO"
    difficulty: str = "STANDARD"
    style: str = "GRITTY_SURVIVAL"
    length: str = "SAGA"
    no_fly_list: List[str] = []

class FrameworkRequest(BaseModel):
    characters: List[dict]
    world_state: dict
    settings: dict
    history: Optional[List[dict]] = None
    context_packet: Optional[dict] = None

@app.post("/api/weaver/framework", response_model=CampaignFramework)
async def create_campaign_framework(request: FrameworkRequest):
    try:
        framework = await generate_campaign_framework(
            characters=request.characters,
            world_state=request.world_state,
            settings=request.settings,
            history=request.history,
            context_packet=request.context_packet
        )
        return framework
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weaver/arc", response_model=List[QuestNode])
async def create_regional_arc(saga_beat: dict, region_context: dict, context_packet: Optional[dict] = None):
    try:
        return await generate_regional_arc(saga_beat, region_context, context_packet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weaver/sidequest", response_model=QuestNode)
async def create_sidequest(hex_context: dict, context_packet: Optional[dict] = None):
    try:
        return await generate_local_sidequest(hex_context, context_packet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weaver/errand", response_model=QuestNode)
async def create_errand(location: str):
    try:
        return await generate_tactical_errand(location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class POIRequest(BaseModel):
    quest_node: dict
    grid_data: list

@app.post("/api/weaver/place_poi")
async def place_poi(request: POIRequest):
    try:
        from core.poi_placer import POIPlacer
        placer = POIPlacer()
        result = placer.place_node_on_grid(request.quest_node, request.grid_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/encounter/generate", response_model=EncounterResponse)
async def api_generate_encounter(request: EncounterRequest):
    try:
        # The generator handles both random and prompted logic
        result = generate_encounter(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        player_sprite=request.composite_sprite,
        difficulty=request.difficulty,
        style=request.style,
        length_type=request.length,
        no_fly_list=json.dumps(request.no_fly_list),
        # 4-Layer Hierarchy Initial Positions
        current_layer=1,
        current_region_x=10, current_region_y=10,
        current_local_x=50, current_local_y=50,
        current_player_x=50, current_player_y=50
    )
    db.add(new_campaign)
    
    weaver_request = {
        "characters": [request.composite_sprite] if request.composite_sprite else [{"name": "Lone Traveler"}],
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
        
        # INITIAL LANDING
        try:
            assembler = ContextAssembler()
            context = await assembler.assemble(campaign_id, request.starting_hex_id, "MORNING", 0)
            biome = context["location"]["biome"]
            # Fix: Correctly pass biome, hex_id, lx, ly, active_npcs, and player_sprite. 
            initial_encounter = TacticalGenerator.generate_ambient_encounter(
                biome,
                request.starting_hex_id,
                new_campaign.current_local_x,
                new_campaign.current_local_y,
                current_hour=PHASE_HOURS["MORNING"],
                densities=(new_campaign.hex_densities or {}).get(str(request.starting_hex_id), {"bandit": 0.1}),
                active_npcs=context.get("active_npcs", []),
                player_sprite=request.composite_sprite
            )
            new_campaign.active_encounter = initial_encounter
        except Exception as e:
            print(f"[DIRECTOR ERROR] Failed to generate initial encounter: {e}")
            # Fallback empty encounter if generation fails
            new_campaign.active_encounter = {"encounter_id": "error_fallback", "tokens": [], "grid": []}

        if hero_journey:
            first_beat = hero_journey[0]
            # Normalize stage name (check for stage_name or title)
            s_name = first_beat.get("stage_name") or first_beat.get("title") or "Call to Adventure"
            new_quest = ActiveQuest(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                title=s_name,
                objectives=[{"objective": first_beat.get("narrative_objective", ""), "is_complete": False}]
            )
            db.add(new_quest)

    db.commit()
    
    arrival_input = {
        "campaign_id": campaign_id,
        "player_id": request.player_id,
        "player_input": "INITIAL_LANDING" 
    }
    
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
        "current_layer": getattr(campaign, 'current_layer', 1),
        "current_region_x": getattr(campaign, 'current_region_x', 10),
        "current_region_y": getattr(campaign, 'current_region_y', 10),
        "current_local_x": getattr(campaign, 'current_local_x', 50),
        "current_local_y": getattr(campaign, 'current_local_y', 50),
        "current_player_x": getattr(campaign, 'current_player_x', 50),
        "current_player_y": getattr(campaign, 'current_player_y', 50),
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
        "pacing_goal": campaign.pacing_goal,
        "active_encounter": campaign.active_encounter
    }

    final_output = await director_graph.ainvoke(initial_state)

    campaign.current_hex = int(final_output["current_location"])
    campaign.current_layer = final_output.get("current_layer", 1)
    campaign.current_region_x = final_output.get("current_region_x", 10)
    campaign.current_region_y = final_output.get("current_region_y", 10)
    campaign.current_local_x = final_output.get("current_local_x", 50)
    campaign.current_local_y = final_output.get("current_local_y", 50)
    campaign.current_player_x = final_output.get("current_player_x", 50)
    campaign.current_player_y = final_output.get("current_player_y", 50)
    
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
        "current_layer": campaign.current_layer,
        "coordinates": {
            "region": [campaign.current_region_x, campaign.current_region_y],
            "local": [campaign.current_local_x, campaign.current_local_y],
            "player": [campaign.current_player_x, campaign.current_player_y]
        },
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

@app.get("/api/world/region/{hex_id}")
async def get_region_map(hex_id: int):
    """Tier 2: 20x20 Regional Strategic Grid."""
    # Assuming biome is retrieved from somewhere, defaulting to Forest for now
    return TacticalGenerator.generate_region_map("Forest", hex_id)

@app.get("/api/world/local/{hex_id}")
async def get_local_grid(hex_id: int, rx: int, ry: int):
    """Tier 3: 100x100 Local Exploration Grid."""
    return TacticalGenerator.generate_local_grid("Forest", hex_id, rx, ry)

@app.get("/api/world/tactical/{hex_id}")
async def get_tactical_grid(hex_id: int, lx: int, ly: int, campaign_id: str = "DEFAULT"):
    """Tier 4: 100x100 Player/Tactical Grid with building interiors and NPCs."""
    db = SessionLocal()
    try:
        state = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
        phase = state.day_phase if state else "MORNING"
        current_hour = PHASE_HOURS.get(phase, 12.0)
        
        # Pull densities for this hex
        densities = (state.hex_densities or {}).get(str(hex_id), {"bandit": 0.2}) if state else {"bandit": 0.1}
        
        assembler = ContextAssembler()
        # Tick is not easily available here, defaulting to 0 or could be pulled from state if added later
        context = await assembler.assemble(campaign_id, hex_id, phase, 0)
        biome = context["location"]["biome"]
        active_npcs = context.get("active_npcs", [])
        player_sprite = state.player_sprite if state else None

        return TacticalGenerator.generate_ambient_encounter(
            biome,
            hex_id,
            lx,
            ly,
            current_hour=current_hour,
            densities=densities,
            active_npcs=active_npcs,
            player_sprite=player_sprite
        )
    finally:
        db.close()

@app.post("/api/travel/plan")
async def plan_travel(request: Request):
    """Calculates path and time for travel across layers."""
    data = await request.json()
    layer = data.get("layer")
    hex_id = data.get("hex_id")
    start = tuple(data.get("start"))
    end = tuple(data.get("end"))

    if layer == "REGIONAL":
        grid_data = TacticalGenerator.generate_region_map("Forest", hex_id)
        return Pathfinder.plan_regional_path(grid_data, start, end)
    elif layer == "LOCAL":
        rx = data.get("rx", 0)
        ry = data.get("ry", 0)
        grid_data = TacticalGenerator.generate_local_grid("Forest", hex_id, rx, ry)
        return Pathfinder.plan_local_path(grid_data, start, end)
    
    raise HTTPException(status_code=400, detail="Unsupported layer or missing parameters")

@app.post("/api/encounter/move")
async def move_token(payload: dict):
    campaign_id = payload.get("campaign_id")
    token_id = payload.get("token_id")
    target_x = payload.get("x")
    target_y = payload.get("y")
    
    db = SessionLocal()
    campaign = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
    if not campaign:
        db.close()
        return {"error": "Campaign not found"}
        
    # Update token position in active_encounter
    encounter = campaign.active_encounter
    if encounter and "tokens" in encounter:
        found = False
        for token in encounter["tokens"]:
            if token["id"] == token_id:
                token["x"] = target_x
                token["y"] = target_y
                found = True
                break
        
        if found:
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(campaign, "active_encounter")
            db.commit()
    
    db.close()
    return {"status": "success"}

@app.get("/api/campaign/load/{campaign_id}")
async def load_campaign(campaign_id: str):
    db = SessionLocal()
    campaign = db.query(CampaignState).filter(CampaignState.id == campaign_id).first()
    db.close()
    if campaign:
        return {
            "current_hex": campaign.current_hex,
            "current_layer": getattr(campaign, 'current_layer', 1),
            "coordinates": {
                "region": [getattr(campaign, 'current_region_x', 10), getattr(campaign, 'current_region_y', 10)],
                "local": [getattr(campaign, 'current_local_x', 50), getattr(campaign, 'current_local_y', 50)],
                "player": [getattr(campaign, 'current_player_x', 50), getattr(campaign, 'current_player_y', 50)]
            },
            "tension": campaign.tension,
            "weather": campaign.weather,
            "chaos_numbers": json.loads(campaign.chaos_numbers),
            "pacing": {"current": campaign.pacing_current, "goal": campaign.pacing_goal},
            "active_encounter": campaign.active_encounter
        }
    return {"error": "NotFound"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
