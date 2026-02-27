from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import CharacterBuildRequest, CompiledCharacterSheet, DerivedVitals, CoreAttributes, CompiledSkill
from core.calc_vitals import calculate_pools
from core.calc_evolution import apply_biology
from core.calc_loadout import apply_holding_fees
from core.calc_skills import calculate_skills, load_tactical_triads
from core.calc_magic import calculate_magic
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
        # 1. Apply Biological Evolutions (Initializes Base and adds Bio Bonuses)
        bio_results = apply_biology(request.evolutions)
        bio_stats = bio_results["updated_stats"]
        granted_passives = bio_results["passives"]
        
        # 2. Calculate Tactical Skill Bonuses and Ranks
        skill_results = calculate_skills(bio_stats, request.tactical_skills)
        compiled_skills = skill_results["skills"]
        skill_bonuses = skill_results["stat_bonuses"]
        
        # 3. Sum everything into the Final Attributes
        final_stats_dict = bio_stats.model_dump()
        for stat, bonus in skill_bonuses.items():
            if stat in final_stats_dict:
                final_stats_dict[stat] += bonus
            
        final_attributes = CoreAttributes(**final_stats_dict)
        
        # 4. Re-calculate Skill Ranks using Final Attributes (Rank = Stat / 5)
        for s_name, s_data in compiled_skills.items():
            skill_info = next(
                (sk for triad in load_tactical_triads().values() for sk in triad if sk["skill"] == s_name), 
                None
            )
            if skill_info:
                parts = [p.strip().lower() for p in skill_info["stat_pair"].split("+")]
                body_stat = "reflexes" if parts[0] == "reflex" else parts[0]
                mind_stat = "reflexes" if parts[1] == "reflex" else parts[1]
                
                # Resolving attribute vs dict access
                lead_pref = s_data["lead"]
                lead_stat = body_stat if lead_pref.lower() == "body" else mind_stat
                
                lead_val = getattr(final_attributes, lead_stat, 10)
                s_data["rank"] = lead_val // 5
                s_data["pips"] = lead_val % 5
        
        # 5. Calculate Survival Pools (HP, Stamina, Composure, Focus)
        vitals = calculate_pools(final_attributes)
        
        # 6. Apply Loadout Holding Fees
        fees = apply_holding_fees(vitals, request.equipped_loadout)
        
        # 7. Process and Validate Schools of Power
        compiled_powers = calculate_magic(final_attributes, request.selected_powers)
        
        # 8. Compile the Final Sheet
        return CompiledCharacterSheet(
            name=request.name,
            attributes=final_attributes,
            vitals=vitals,
            evolutions=request.evolutions,
            passives=granted_passives,
            tactical_skills=compiled_skills,
            powers=compiled_powers,
            loadout=request.equipped_loadout,
            holding_fees=fees
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
