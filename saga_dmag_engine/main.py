from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import SpellCastRequest, SpellCastResolution
from core.resonance_logic import calculate_resonance
from core.volatility_resolver import resolve_volatility
import uvicorn

app = FastAPI(title="S.A.G.A. DMAg Engine", description="Tactical Magic & D-Dust Resolver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "module": "DMAg Engine", "port": 8008}

@app.post("/api/magic/resolve", response_model=SpellCastResolution)
def resolve_magic(req: SpellCastRequest) -> SpellCastResolution:
    # 1. Calculate Resonance
    biome = req.environment_context.get("biome", "Wilderness")
    weather = req.environment_context.get("weather", "Clear Skies")
    res_bonus, res_flavor = calculate_resonance(req.school, biome, weather)
    
    # 2. Calculate Volatility (if D-Dust used)
    vol_strike, vol_flavor = resolve_volatility(req.dust_amount, req.chaos_level)
    
    # 3. Final Intensity & Focus Cost
    final_intensity = req.base_intensity + res_bonus
    if vol_strike:
        final_intensity = max(0, final_intensity // 2) # Misfire cuts power by half
        
    # Overcharge: Each D-Dust adds raw intensity
    final_intensity += req.dust_amount
    
    # Calculate Focus Cost (Base + Intensity scaling)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
