"""
Saga Architect — World Simulation Microservice
Thin HTTP API adapter. All simulation logic lives in saga_chronos/engine.py.
This service:
  1. On /api/world/init: fetches faction seeds from saga_lore_module, 
     seeds the Chronos engine state, triggers first tick.
  2. On /api/world/tick: calls ChronosEngine.run_tick(N) via direct import.
  3. On /api/world/inject_events: applies Chronicle Ledger events to Chronos state.
  4. On /api/world/snapshot: returns current world state for debugging.
"""

import json
import os
import sys
import uuid
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Import the Chronos engine directly ───────────────────────────────────────
CHRONOS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "saga_chronos")
)
if CHRONOS_PATH not in sys.path:
    sys.path.insert(0, CHRONOS_PATH)

from engine import ChronosEngine  # noqa: E402

from core.models import Base, WorldState, FactionRecord
from core.schemas import (
    InitWorldRequest, TickRequest, InjectEventsRequest,
    WorldSnapshot, FactionState, ExportResponse
)
from core.simulator import apply_events_to_state, export_to_json

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Saga Architect – World Simulation Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = "sqlite:///saga_world.db"
db_engine    = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=db_engine)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_MAP_PATH    = os.getenv("SAGA_WORLD_MAP_PATH",  "../data/Saga_Master_World.json")
EXPORT_PATH      = BASE_MAP_PATH
LORE_MODULE_URL  = os.getenv("LORE_MODULE_URL",      "http://localhost:8005")

# ── Singleton Chronos engine (shared across requests) ─────────────────────────
_chronos: ChronosEngine | None = None

def get_chronos() -> ChronosEngine:
    global _chronos
    if _chronos is None:
        _chronos = ChronosEngine()
    return _chronos


# ── DB helpers ────────────────────────────────────────────────────────────────
def _load_snapshot(db, campaign_id: str) -> WorldSnapshot | None:
    ws = db.query(WorldState).filter(WorldState.campaign_id == campaign_id).first()
    if not ws:
        return None
    factions = db.query(FactionRecord).filter(FactionRecord.campaign_id == campaign_id).all()
    return WorldSnapshot(
        campaign_id=campaign_id,
        tick_count=ws.tick_count,
        year=ws.year,
        season=ws.season,
        factions=[
            FactionState(
                id=f.id,
                name=f.name,
                faction_type=f.faction_type,
                military_strength=f.military_strength,
                food_supply=f.food_supply,
                territory_hex_ids=f.territory_hex_ids or [],
                at_war_with=f.at_war_with or [],
                is_expanding=bool(f.is_expanding),
                is_starving=bool(f.is_starving),
            )
            for f in factions
        ],
        hex_overrides=ws.hex_overrides or {},
    )


def _save_snapshot(db, snapshot: WorldSnapshot):
    ws = db.query(WorldState).filter(WorldState.campaign_id == snapshot.campaign_id).first()
    if not ws:
        ws = WorldState(id=str(uuid.uuid4()), campaign_id=snapshot.campaign_id)
        db.add(ws)
    ws.tick_count    = snapshot.tick_count
    ws.year          = snapshot.year
    ws.season        = snapshot.season
    ws.hex_overrides = snapshot.hex_overrides

    for fs in snapshot.factions:
        fr = db.query(FactionRecord).filter(FactionRecord.id == fs.id).first()
        if not fr:
            fr = FactionRecord(id=fs.id, campaign_id=snapshot.campaign_id)
            db.add(fr)
        fr.name              = fs.name
        fr.faction_type      = fs.faction_type
        fr.military_strength = fs.military_strength
        fr.food_supply       = fs.food_supply
        fr.territory_hex_ids = fs.territory_hex_ids
        fr.at_war_with       = fs.at_war_with
        fr.is_expanding      = int(fs.is_expanding)
        fr.is_starving       = int(fs.is_starving)

    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "Architect online", "chronos": "ready" if _chronos else "unloaded"}


@app.post("/api/world/init")
async def init_world(req: InitWorldRequest):
    """
    Initialize a new campaign's world state.
    1. Fetches faction data from saga_lore_module if no seeds are provided.
    2. Seeds the Chronos engine state dictionary with starting factions.
    3. Runs the first 30-day global tick to establish initial conditions.
    """
    db = SessionLocal()

    # Wipe existing state for this campaign
    existing = db.query(WorldState).filter(WorldState.campaign_id == req.campaign_id).first()
    if existing:
        db.query(FactionRecord).filter(FactionRecord.campaign_id == req.campaign_id).delete()
        db.delete(existing)
        db.commit()

    # ── Fetch faction seeds from lore module if none provided ──────────────
    faction_seeds = req.faction_seeds or []
    if not faction_seeds:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{LORE_MODULE_URL}/api/lore/entities")
                if resp.status_code == 200:
                    lore_data = resp.json()
                    for faction_lore in lore_data.get("factions", []):
                        stats = faction_lore.get("stats", {})
                        faction_seeds.append(FactionState(
                            id=str(uuid.uuid4()),
                            name=faction_lore.get("name", "Unknown Faction"),
                            faction_type="POLITICAL_FACTION",
                            military_strength=float(stats.get("military_strength", 50)),
                            food_supply=float(stats.get("food_supply", 200)),
                            territory_hex_ids=stats.get("territory_hex_ids", []),
                            at_war_with=[],
                            is_expanding=False,
                            is_starving=False,
                        ))
                    print(f"[ARCHITECT] Loaded {len(faction_seeds)} factions from Lore Module.")
        except Exception as e:
            print(f"[ARCHITECT] Warning: Could not fetch from lore module: {e}")

    # ── Seed Chronos engine with faction data ──────────────────────────────
    chronos = get_chronos()
    chronos.state["factions"] = {}
    for fs in faction_seeds:
        chronos.state["factions"][fs.name] = {
            "resources": {
                "food": fs.food_supply,
                "wood": 50.0, "stone": 30.0,
                "iron": 10.0, "copper": 5.0,
                "gold": 5.0,  "nickel": 0.0,
                "clay": 10.0, "hide": 5.0,
                "dragonstone": 0.0, "d_dust": 0.0,
                "atherium_coin": 0.0,
                "ichor_honey": 0.0, "voltaic_fleece": 0.0,
                "ozone_milk": 0.0, "lith_weave": 0.0,
                "aether_clear": 0.0, "avian_silk": 0.0,
            },
            "population":        1000,
            "military_strength": fs.military_strength,
            "buildings":         ["hearth", "storage_pit"],
            "tier":              0,
            "unrest":            0,
            "at_war_with":       fs.at_war_with,
            "trade_routes":      [],
        }
    chronos.state["current_tick"] = 0
    chronos.save_state()

    # ── Save DB snapshot ───────────────────────────────────────────────────
    snapshot = WorldSnapshot(
        campaign_id=req.campaign_id,
        tick_count=0,
        year=1,
        season="Spring",
        factions=faction_seeds,
        hex_overrides={}
    )
    _save_snapshot(db, snapshot)
    db.close()

    # ── Run first 30-day tick to establish world ───────────────────────────
    chronos.run_tick(days_to_advance=30)

    return {
        "status": "initialized",
        "campaign_id": req.campaign_id,
        "factions": len(faction_seeds),
        "faction_names": [f.name for f in faction_seeds],
    }


@app.post("/api/world/tick")
async def tick_world(req: TickRequest):
    """
    Advance the world simulation by N days (default 30 = one month).
    Called after a Long Rest or at Saga Stage advancement.
    """
    db       = SessionLocal()
    snapshot = _load_snapshot(db, req.campaign_id)
    if not snapshot:
        db.close()
        raise HTTPException(status_code=404, detail=f"No world state for campaign {req.campaign_id}. Call /api/world/init first.")

    chronos   = get_chronos()
    days      = req.ticks * 30  # Each "tick" = 30 in-world days
    date_info = chronos.run_tick(days_to_advance=days)

    # Sync Chronos state back into the DB snapshot
    snapshot.tick_count = chronos.state["current_tick"]
    snapshot.year       = date_info.get("year", snapshot.year)
    snapshot.season     = date_info.get("season", snapshot.season)

    # Update faction states in snapshot from Chronos state
    for fs in snapshot.factions:
        chrono_f = chronos.state["factions"].get(fs.name, {})
        if chrono_f:
            r = chrono_f.get("resources", {})
            fs.food_supply       = float(r.get("food", fs.food_supply))
            fs.military_strength = float(chrono_f.get("military_strength", fs.military_strength))
            fs.is_starving       = r.get("food", 100) < 20.0
            fs.at_war_with       = chrono_f.get("at_war_with", [])

    _save_snapshot(db, snapshot)
    db.close()

    # Export fresh world JSON for Weaver
    export_to_json(snapshot, BASE_MAP_PATH, EXPORT_PATH)

    return {
        "status":      "ticked",
        "ticks_run":   req.ticks,
        "days_passed":  days,
        "year":        date_info.get("year", snapshot.year),
        "month":       date_info.get("month", "Unknown"),
        "season":      date_info.get("season", snapshot.season),
        "moon_phase":  date_info.get("moon", {}).get("primary", {}).get("orbital_phase", "Unknown"),
        "chaos_modifier": date_info.get("chaos_modifier", 1.0),
        "is_shadow_week": date_info.get("is_shadow_week", False),
        "factions": [
            {
                "name":     f.name,
                "starving": f.is_starving,
                "at_war":   len(f.at_war_with) > 0,
                "military": f.military_strength,
            }
            for f in snapshot.factions
        ],
    }


@app.post("/api/world/inject_events")
async def inject_events(req: InjectEventsRequest):
    """
    Inject Chronicle Ledger events from saga_director before the next tick.
    Player actions (routed a faction, aided a village) mutate the world state.
    """
    db       = SessionLocal()
    snapshot = _load_snapshot(db, req.campaign_id)
    if not snapshot:
        db.close()
        return {"error": "No world state found."}

    snapshot = apply_events_to_state(snapshot, req.events)

    # Also apply events to Chronos state for continuity
    chronos = get_chronos()
    for ev in req.events:
        desc   = (ev.get("event_description") or "").lower()
        assoc  = ev.get("associated_faction")
        if assoc and assoc in chronos.state.get("factions", {}):
            f = chronos.state["factions"][assoc]
            if "routed" in desc or "defeated" in desc:
                f["military_strength"] = max(0.0, f.get("military_strength", 50) - 25.0)
            if "slain" in desc and "leader" in desc:
                f["military_strength"] = max(0.0, f.get("military_strength", 50) - 40.0)

    _save_snapshot(db, snapshot)
    db.close()
    return {"status": "events_applied", "event_count": len(req.events)}


@app.get("/api/world/snapshot/{campaign_id}")
async def get_snapshot(campaign_id: str):
    """Return current world state as JSON for debugging."""
    db       = SessionLocal()
    snapshot = _load_snapshot(db, campaign_id)
    db.close()
    if not snapshot:
        return {"error": "No world state found."}

    # Enrich with live Chronos state
    chronos = get_chronos()
    date    = chronos.clock.get_current_date(chronos.state["current_tick"])

    return {
        **snapshot.model_dump(),
        "calendar": date,
        "chronos_factions": chronos.state.get("factions", {}),
    }


@app.post("/api/world/export/{campaign_id}")
async def export_world(campaign_id: str):
    """Force export world state JSON for the Weaver."""
    db       = SessionLocal()
    snapshot = _load_snapshot(db, campaign_id)
    db.close()
    if not snapshot:
        return {"error": "No world state found."}
    export_to_json(snapshot, BASE_MAP_PATH, EXPORT_PATH)
    return {"status": "exported", "path": EXPORT_PATH}
