from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import ClashRequest, ClashResolution
from core.clash_calculator import resolve_clash
from core.injury_applier import apply_injuries

app = FastAPI(
    title="S.A.G.A. Clash Engine",
    description="Blueprint 07 — The Rules Manager. Stateless, no-database calculator for contested combat.  There is no Armor Class here.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "module": "Clash Engine", "port": 8007}


@app.post("/api/clash/resolve", response_model=ClashResolution)
def resolve(req: ClashRequest) -> ClashResolution:
    """
    Resolve a combat clash between an attacker and a defender.

    Flow:
    1. clash_calculator.py rolls 1d20 for both sides.
    2. Each total = roll + pool + stamina_burned.
    3. margin = atk_total - def_total.
    4. Margin-of-Victory thresholds determine the result.
    5. injury_applier.py checks if the blow was lethal (dropped to 0 HP)
       and assigns a Dual-Track Injury slot.
    6. Final ClashResolution JSON is returned to the Saga Director App.
    """
    # 1. Calculate the raw damage and margin
    resolution = resolve_clash(req)
    
    # 2. Pass BOTH the resolution and original request to check for lethal blows
    resolution = apply_injuries(resolution, req)
    
    return resolution
