from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import CharacterBuildRequest, CompiledCharacterSheet, DerivedVitals, CoreAttributes, CompiledSkill
from core.calc_vitals import calculate_pools
from core.calc_evolution import apply_biology
from core.calc_loadout import apply_holding_fees
from core.calc_skills import calculate_skills, load_tactical_triads
from core.calc_magic import calculate_magic
from saga_common.models.core import PipBank

# Imported from old Item Engine
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.economy_engine import calculate_d_dust_rate
from core.effect_resolver import resolve_consumable
from core.data_loader import load_item_by_id

# Imported from old Skill Engine
from core.schemas import SkillCheckRequest, SkillCheckResult
from core.dice_roller import roll_d20
from core.pip_calculator import check_for_pips

# Imported from old Clash and DMAG Engines
from core.clash_schemas import ClashRequest, ClashResolution
from core.clash_calculator import resolve_clash
from core.injury_applier import apply_injuries
from core.dmag_schemas import SpellCastRequest, SpellCastResolution
from core.resonance_logic import calculate_resonance
from core.volatility_resolver import resolve_volatility

import uvicorn

app = FastAPI(title="T.A.L.E.W.E.A.V.E.R. Rules Engine", version="1.0.0")

class EconomyRequest(BaseModel):
    base_rate: float = 10.0
    chaos_level: int = 1

class ResolveRequest(BaseModel):
    item_id: str
    target_vitals: Optional[Dict[str, Any]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "module": "Rules Engine", "port": 8014}

@app.post("/api/rules/economy/rate")
async def get_economy_rate(request: EconomyRequest):
    """
    Returns the current D-Dust to Aetherium exchange rate.
    """
    rate = calculate_d_dust_rate(request.base_rate, request.chaos_level)
    return {"exchange_rate": rate, "unit": "1g D-Dust = X Aetherium"}

@app.post("/api/rules/items/resolve")
async def resolve_item_effect(request: ResolveRequest):
    """
    Resolves the mathematical result of using an item by its ID.
    Strict isolation rule: it takes an Item ID and returns a math output.
    """
    item_data = load_item_by_id(request.item_id)
    if not item_data:
        raise HTTPException(status_code=404, detail=f"Item ID '{request.item_id}' not found.")

    try:
        result = resolve_consumable(item_data, request.target_vitals)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/rules/clash/resolve", response_model=ClashResolution)
def resolve_combat_clash(req: ClashRequest) -> ClashResolution:
    """
    Resolve a combat clash between an attacker and a defender.
    """
    resolution = resolve_clash(req)
    resolution = apply_injuries(resolution, req)
    return resolution

@app.post("/api/rules/magic/resolve", response_model=SpellCastResolution)
def resolve_magic(req: SpellCastRequest) -> SpellCastResolution:
    """
    Resolve Tactical Magic & D-Dust usage.
    """
    biome = req.environment_context.get("biome", "Wilderness")
    weather = req.environment_context.get("weather", "Clear Skies")
    res_bonus, res_flavor = calculate_resonance(req.school, biome, weather)

    vol_strike, vol_flavor = resolve_volatility(req.dust_amount, req.chaos_level)

    final_intensity = req.base_intensity + res_bonus
    if vol_strike:
        final_intensity = max(0, final_intensity // 2)

    final_intensity += req.dust_amount
    focus_cost = 2 + (final_intensity * 2)

    math_log = f"[MAGIC] {req.spell_name} ({req.school}). Res: {'+' if res_bonus >= 0 else ''}{res_bonus}. Dust: +{req.dust_amount}."
    if vol_strike:
        math_log += " [VOLATILITY STRIKE!]"

    return SpellCastResolution(
        final_intensity=final_intensity,
        focus_cost=focus_cost,
        volatility_strike=vol_strike,
        volatility_narrative=vol_flavor,
        resonance_bonus=res_bonus,
        resonance_narrative=res_flavor,
        math_log=math_log
    )

@app.post("/api/rules/skills/roll", response_model=SkillCheckResult)
def roll_skill_check(req: SkillCheckRequest) -> SkillCheckResult:
    """
    Resolve a skill check.
    """
    raw_die, _ = roll_d20(
        is_advantage=req.roll_state.is_advantage,
        is_disadvantage=req.roll_state.is_disadvantage
    )

    # Total = d20 + Lead Stat + Trail Stat + Skill Rank + Focus Spent
    roll_total = (
        raw_die
        + req.lead_stat_value
        + req.trail_stat_value
        + req.skill_rank
        + req.roll_state.focus_spent
    )

    is_success = roll_total >= req.target_dc
    margin = roll_total - req.target_dc

    pip_trigger = check_for_pips(
        raw_die=raw_die,
        is_success=is_success,
        is_life_or_death=req.is_life_or_death
    )

    return SkillCheckResult(
        roll_total=roll_total,
        raw_die_face=raw_die,
        is_success=is_success,
        margin=margin,
        scars_and_stars_trigger=pip_trigger
    )

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
            pip_bank=request.pip_bank,
            composite_sprite=request.composite_sprite
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
        # For now, just deduct the pip. The actual recovery is handled by the VTT/Director state.
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
    uvicorn.run(app, host="0.0.0.0", port=8014)
