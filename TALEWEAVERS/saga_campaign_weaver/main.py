from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from core.schemas import CampaignRoadmap
from core.weaver import generate_roadmap

app = FastAPI(title="S.A.G.A. Campaign Weaver", version="1.0.0")

class GenerateRequest(BaseModel):
    world_id: str = Field(..., description="The ID of the world generation to use")
    starting_hex: str = Field(..., description="The hex ID where the campaign starts")
    theme_preference: Optional[str] = Field(None, description="E.g., 'Grimdark', 'Heroic Fantasy'")

@app.get("/")
async def root():
    return {"module": "Campaign Weaver", "status": "Online", "port": 8010}

class SideQuestRequest(BaseModel):
    seed: str = Field(..., description="The story seed or prompt for the side quest")
    location: str = Field(..., description="Where this side quest takes place")

@app.post("/api/weaver/side_quest", response_model=QuestNode)
async def generate_side_quest(request: SideQuestRequest):
    try:
        from core.weaver import generate_mini_quest
        quest = await generate_mini_quest(request.seed, request.location)
        return quest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
