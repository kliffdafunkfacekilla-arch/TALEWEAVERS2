from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import EncounterRequest, EncounterResponse
from core.generator import generate_encounter

app = FastAPI(title="S.A.G.A. Encounter Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"module": "Encounter Engine", "status": "Online", "port": 8009}

@app.post("/api/encounter/generate", response_model=EncounterResponse)
async def api_generate_encounter(request: EncounterRequest):
    try:
        # The generator handles both random and prompted logic
        result = generate_encounter(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
