from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import SkillCheckRequest, SkillCheckResult
from core.dice_roller import roll_d20
from core.pip_calculator import check_for_pips

app = FastAPI(
    title="S.A.G.A. Skill Engine",
    description="Blueprint 06 — The Fate Engine. Stateless, dice-rolling calculator for all non-combat friction.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "module": "Skill Engine", "port": 8006}


@app.post("/api/skills/roll", response_model=SkillCheckResult)
def roll_skill_check(req: SkillCheckRequest) -> SkillCheckResult:
    """
    Resolve a skill check.

    Flow:
    1. dice_roller.py rolls 1d20 (rolling twice if Advantage/Disadvantage).
    2. It adds the lead_stat_value, trail_stat_value, and skill_rank.
    3. It checks pip_calculator.py using the raw die face.
    4. Returns the final JSON to the Saga Director App.
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
