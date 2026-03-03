from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import CharacterBuildRequest, CompiledCharacterSheet, DerivedVitals, CoreAttributes, CompiledSkill
from core.calc_vitals import calculate_pools
from core.calc_evolution import apply_biology
from core.calc_loadout import apply_holding_fees
from core.calc_skills import calculate_skills, load_tactical_triads
from core.calc_magic import calculate_magic
from saga_common.models.core import PipBank
import uvicorn
from typing import Dict, Any

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
                # Normalizing skill ranks based on lead stat
                lead_pref = s_data["lead"]
                # skill_info["stat_pair"] looks like "Might + Knowledge"
                stats_in_pair = [s.strip().lower() for s in skill_info["stat_pair"].split("+")]
                
                # Identify which is Body and which is Mind
                BODY_STATS = {"might", "endurance", "vitality", "fortitude", "reflexes", "finesse"}
                
                body_stat = next((s for s in stats_in_pair if s in BODY_STATS), stats_in_pair[0])
                mind_stat = next((s for s in stats_in_pair if s not in BODY_STATS), stats_in_pair[1])
                
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
            holding_fees=fees,
            pip_bank=request.pip_bank
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rules/character/evolve", response_model=CompiledCharacterSheet)
async def evolve_character(
    sheet: CompiledCharacterSheet = Body(...),
    expenditure: Dict[str, Any] = Body(...)
):
    """
    Handles spending STAR, SCAR, and SURVIVOR pips.
    Expenditure format: {"type": "STAR", "target": "might"} or {"type": "SCAR", "target": "Assault"}
    """
    pips = sheet.pip_bank
    etype = expenditure.get("type")
    target = expenditure.get("target")

    if etype == "STAR":
        if pips.stars <= 0:
            raise HTTPException(status_code=400, detail="No STAR pips available.")
        if hasattr(sheet.attributes, target):
            setattr(sheet.attributes, target, getattr(sheet.attributes, target) + 1)
            pips.stars -= 1
        else:
            raise HTTPException(status_code=400, detail=f"Invalid attribute target: {target}")

    elif etype == "SCAR":
        if pips.scars <= 0:
            raise HTTPException(status_code=400, detail="No SCAR pips available.")
        if target in sheet.tactical_skills:
            # In TALEWEAVERS, spending a SCAR on a skill increases the underlying LEAD attribute 
            # (which indirectly raises rank/pips). Or we can directly boost rank for simplicity?
            # Design choice: SCARs are "painful lessons" - they boost the Skill specifically.
            # Let's say it adds +1 to the LEAD stat used for that skill.
            skill_data = sheet.tactical_skills[target]
            # We need to find the lead stat for this skill
            skill_info = next(
                (sk for triad in load_tactical_triads().values() for sk in triad if sk["skill"] == target), 
                None
            )
            if skill_info:
                stats_in_pair = [s.strip().lower() for s in skill_info["stat_pair"].split("+")]
                BODY_STATS = {"might", "endurance", "vitality", "fortitude", "reflexes", "finesse"}
                body_stat = next((s for s in stats_in_pair if s in BODY_STATS), stats_in_pair[0])
                mind_stat = next((s for s in stats_in_pair if s not in BODY_STATS), stats_in_pair[1])
                lead_stat = body_stat if skill_data.lead.lower() == "body" else mind_stat
                
                setattr(sheet.attributes, lead_stat, getattr(sheet.attributes, lead_stat) + 1)
                pips.scars -= 1
            else:
                 raise HTTPException(status_code=400, detail=f"Skill info not found: {target}")
        else:
            raise HTTPException(status_code=400, detail=f"Skill not found on sheet: {target}")

    elif etype == "SURVIVOR":
        if pips.survivors <= 0:
            raise HTTPException(status_code=400, detail="No SURVIVOR pips available.")
        # Survivors act as a "Full Recovery" of a pool
        # For now, just deduct the pip. The actual recovery is handled by the VTT/GM state.
        pips.survivors -= 1
    
    # Re-calculate derived values
    sheet.vitals = calculate_pools(sheet.attributes)
    
    # Re-calculate all skill ranks/pips
    for s_name, s_data in sheet.tactical_skills.items():
        skill_info = next((sk for triad in load_tactical_triads().values() for sk in triad if sk["skill"] == s_name), None)
        if skill_info:
             stats_in_pair = [s.strip().lower() for s in skill_info["stat_pair"].split("+")]
             BODY_STATS = {"might", "endurance", "vitality", "fortitude", "reflexes", "finesse"}
             body_stat = next((s for s in stats_in_pair if s in BODY_STATS), stats_in_pair[0])
             mind_stat = next((s for s in stats_in_pair if s not in BODY_STATS), stats_in_pair[1])
             lead_stat = body_stat if s_data.lead.lower() == "body" else mind_stat
             lead_val = getattr(sheet.attributes, lead_stat, 10)
             s_data.rank = lead_val // 5
             s_data.pips = lead_val % 5

    return sheet

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
