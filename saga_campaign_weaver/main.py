from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from core.schemas import CampaignRoadmap, QuestNode, CampaignFramework
from core.weaver import (
    generate_campaign_framework, 
    generate_regional_arc, 
    generate_local_sidequest, 
    generate_tactical_errand
)

app = FastAPI(title="S.A.G.A. Campaign Weaver", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"module": "Campaign Weaver", "status": "Online", "port": 8010}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)
