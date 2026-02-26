import subprocess
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

app = FastAPI(title="TALEWEAVERS World Architect API")

# Allow React (Port 5173) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    world_settings: Dict[str, Any]
    climate: Dict[str, Any]
    biomes: List[Dict[str, Any]]
    factions: List[Any]
    time_rules: Optional[Dict[str, Any]] = None
    flora_fauna: Optional[List[Dict[str, Any]]] = None

# Shared execution function
async def run_cpp_engine(req: GenerateRequest, phase: str):
    print(f"[API] Running phase: {phase}...")
    
    # 1. Write the payload to architect_config.json so C++ can read it
    config_path = "architect_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(req.model_dump(exclude_none=True), f, indent=2)
        
    print("[API] Wrote architect_config.json. Booting C++ Engine...")
    
    # 2. Determine the correct executable path
    executable = "./build/saga_architect"
    if os.path.exists("./build/Debug/saga_architect.exe"):
        executable = "./build/Debug/saga_architect.exe"
    elif os.path.exists("./build/saga_architect.exe"):
         executable = "./build/saga_architect.exe"

    # 3. Pull the trigger on the C++ Engine with the phase argument
    try:
        result = subprocess.run([executable, "--phase", phase], capture_output=True, text=True, check=True)
        print(f"[C++ ENGINE]:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[C++ ERROR]:\n{e.stderr}")
        raise HTTPException(status_code=500, detail="C++ God Engine crashed during simulation.")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Could not find C++ executable at {executable}. Did you compile it?")

    # 4. Read the output and send it back to React
    output_path = "Saga_Master_World.json"
    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Generation failed: Saga_Master_World.json is missing.")
        
    with open(output_path, "r", encoding="utf-8") as f:
        world_data = json.load(f)
        
    print(f"[API] {phase} Success. Returning data to VTT.")
    return {"status": "SUCCESS", "phase": phase, "world_data": world_data}

@app.post("/api/world/generate")
async def generate_full(req: GenerateRequest):
    return await run_cpp_engine(req, "all")

@app.post("/api/world/generate/tectonics")
async def generate_tectonics(req: GenerateRequest):
    return await run_cpp_engine(req, "tectonics")

@app.post("/api/world/generate/climate")
async def generate_climate(req: GenerateRequest):
    return await run_cpp_engine(req, "climate")

@app.post("/api/world/generate/cultures")
async def generate_cultures(req: GenerateRequest):
    return await run_cpp_engine(req, "cultures")

if __name__ == "__main__":
    import uvicorn
    # Module 2 runs on Port 8002!
    uvicorn.run(app, host="0.0.0.0", port=8002)
