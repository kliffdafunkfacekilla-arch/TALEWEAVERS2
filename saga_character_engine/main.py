from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import CharacterBuildRequest, CompiledCharacterSheet, DerivedVitals
from core.calc_vitals import calculate_pools
from core.calc_evolution import apply_biology
from core.calc_loadout import apply_holding_fees
import uvicorn

app = FastAPI(title="T.A.L.E.W.E.A.V.E.R. Character Rules Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "Character Rules Engine", "port": 8003}

@app.post("/api/rules/character/calculate", response_model=CompiledCharacterSheet)
async def calculate_character_sheet(request: CharacterBuildRequest):
    """
    Takes a character build request and returns a compiled character sheet
    with all math, evolutions, and loadout fees applied.
    """
    try:
        # 1. Apply Biological Evolutions (Modifies attributes and adds passives)
        # We work on a copy of attributes to be safe
        mutated_attributes = request.base_attributes.model_copy(deep=True)
        bio_results = apply_biology(mutated_attributes, request.evolutions)
        
        final_attributes = bio_results["updated_stats"]
        granted_passives = bio_results["passives"]
        
        # 2. Calculate Survival Pools (HP, Stamina, Composure, Focus)
        vitals = calculate_pools(final_attributes)
        
        # 3. Apply Loadout Holding Fees
        fees = apply_holding_fees(vitals, request.equipped_loadout)
        
        # 4. Compile the Final Sheet
        return CompiledCharacterSheet(
            name=request.name,
            attributes=final_attributes,
            vitals=vitals,
            evolutions=request.evolutions,
            passives=granted_passives,
            powers=request.selected_powers,
            loadout=request.equipped_loadout,
            holding_fees=fees
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
