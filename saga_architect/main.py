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
import logging
import subprocess
from contextlib import asynccontextmanager
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Import the Chronos engine directly ───────────────────────────────────────
from core.engine import ChronosEngine
from core.chronos_clock import ChronosClock

from core.models import Base, WorldState, FactionRecord
from core.schemas import (
    InitWorldRequest, TickRequest, InjectEventsRequest,
    WorldSnapshot, FactionState, ExportResponse
)
from core.lore_schemas import (
    IngestRequest, IngestResponse, SearchRequest, SearchResponse
)
from pydantic import BaseModel
class AdvanceClockRequest(BaseModel):
    current_tick: int
    days_to_advance: int = 1
from core.simulator import apply_events_to_state, export_to_json
from core.vault_parser import parse_vault
from core.vector_store import LoreVaultDB

logger = logging.getLogger("saga_architect")

MODULE_DIR   = Path(__file__).resolve().parent
BASE_DIR     = MODULE_DIR.parent
OSTRAKA_DIR  = BASE_DIR / "data" / "Ostraka"
ENTITIES_DIR = BASE_DIR / "data" / "entities"

_ingest_status = {
    "state":      "pending",
    "docs_count": 0,
    "categories": {},
    "errors":     [],
    "entity_gen": "pending",
}

lore_db = LoreVaultDB()

def _run_ingest_background():
    global _ingest_status
    try:
        current_count = lore_db.collection.count()

        if current_count > 0:
            logger.info(f"[LORE] ChromaDB already populated ({current_count} docs). Skipping auto-ingest.")
            _ingest_status["state"]      = "complete"
            _ingest_status["docs_count"] = current_count
            _ingest_status["entity_gen"] = "complete"
            return

        if not OSTRAKA_DIR.exists():
            logger.warning(f"[LORE] Ostraka vault not found at {OSTRAKA_DIR}. Skipping auto-ingest.")
            _ingest_status["state"]  = "error"
            _ingest_status["errors"] = [f"Vault directory not found: {OSTRAKA_DIR}"]
            return

        logger.info(f"[LORE] ChromaDB is empty. Auto-ingesting Ostraka vault from {OSTRAKA_DIR}...")
        _ingest_status["state"] = "running"

        documents = parse_vault(str(OSTRAKA_DIR))
        if not documents:
            _ingest_status["state"]  = "error"
            _ingest_status["errors"] = ["No valid markdown files found in the Ostraka vault."]
            return

        lore_db.add_documents(documents)

        categories = [doc["category"] for doc in documents]
        category_counts = dict(Counter(categories))

        _ingest_status["state"]      = "complete"
        _ingest_status["docs_count"] = len(documents)
        _ingest_status["categories"] = category_counts
        logger.info(f"[LORE] Auto-ingest complete: {len(documents)} docs across {len(category_counts)} categories.")

        _kick_entity_generator()

    except Exception as e:
        logger.error(f"[LORE] Auto-ingest failed: {e}")
        _ingest_status["state"]  = "error"
        _ingest_status["errors"] = [str(e)]


def _kick_entity_generator():
    global _ingest_status
    try:
        script_path = MODULE_DIR / "entity_generator.py"
        if not script_path.exists():
            logger.warning("[LORE] entity_generator.py not found — skipping stat-block generation.")
            return

        _ingest_status["entity_gen"] = "running"
        logger.info("[LORE] Launching entity_generator.py in background...")
        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(MODULE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("[LORE] entity_generator.py launched.")
    except Exception as e:
        logger.error(f"[LORE] Could not launch entity_generator.py: {e}")
        _ingest_status["entity_gen"] = "error"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import threading
    thread = threading.Thread(target=_run_ingest_background, daemon=True)
    thread.start()
    yield

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Saga Architect – World Simulation Engine", lifespan=lifespan)
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

# ── Singleton Chronos engine (shared across requests) ─────────────────────────
_chronos: ChronosEngine | None = None

def get_chronos() -> ChronosEngine:
    global _chronos
    if _chronos is None:
        _chronos = ChronosEngine()
    return _chronos

# ── Standalone Clock (from old Chronos Engine) ────────────────────────────────
def load_calendar_config():
    CALENDAR_FILE = os.path.join(MODULE_DIR, "data", "calendar_rules.json")
    if os.path.exists(CALENDAR_FILE):
        try:
            with open(CALENDAR_FILE, "r") as f:
                return json.load(f)
        except Exception: pass
    return {}

_standalone_clock = ChronosClock(load_calendar_config())


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
    return {
        "status": "Architect online",
        "chronos": "ready" if _chronos else "unloaded",
        "ingest_state": _ingest_status["state"],
        "docs_indexed": _ingest_status["docs_count"],
        "entity_gen":   _ingest_status["entity_gen"],
    }

@app.get("/api/config/calendar")
async def get_calendar():
    return load_calendar_config()

@app.post("/api/config/calendar")
async def save_calendar(request: dict):
    global _standalone_clock
    try:
        CALENDAR_FILE = os.path.join(MODULE_DIR, "data", "calendar_rules.json")
        with open(CALENDAR_FILE, "w") as f:
            json.dump(request, f, indent=2)

        # Hot-reload the clock engine with the new rules
        _standalone_clock = ChronosClock(request)

        return {"status": "success", "message": "Calendar rules updated and Chronos restarted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save calendar: {e}")

@app.post("/api/chronos/tick")
async def advance_clock(req: AdvanceClockRequest):
    """
    Advances the standalone clock and returns the new date (Legacy Chronos Endpoint).
    """
    try:
        time_data = _standalone_clock.advance_time(req.current_tick, req.days_to_advance)
        date_data = _standalone_clock.get_current_date(time_data["new_tick"])
        return {
            "status": "success",
            "time_data": time_data,
            "date": date_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lore/ingest_status")
async def ingest_status():
    return {
        **_ingest_status,
        "vault_path":    str(OSTRAKA_DIR),
        "entities_path": str(ENTITIES_DIR),
        "chroma_count":  lore_db.collection.count(),
    }

@app.post("/api/lore/ingest", response_model=IngestResponse)
async def ingest_lore(request: IngestRequest):
    if request.force_rebuild:
        lore_db.wipe_db()
    try:
        documents = parse_vault(request.vault_path)
        if not documents:
            return IngestResponse(
                status="warning", files_processed=0, categories_mapped={},
                errors=["No valid markdown files found in the specified path."]
            )
        lore_db.add_documents(documents)
        categories = [doc["category"] for doc in documents]
        category_counts = dict(Counter(categories))
        _ingest_status["state"]      = "complete"
        _ingest_status["docs_count"] = len(documents)
        _ingest_status["categories"] = category_counts
        _kick_entity_generator()
        return IngestResponse(
            status="success", files_processed=len(documents),
            categories_mapped=category_counts, errors=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lore/search", response_model=SearchResponse)
async def search_lore(request: SearchRequest):
    try:
        results = lore_db.query(
            query_text=request.query,
            top_k=request.top_k,
            filter_categories=[str(c) for c in request.filter_categories] if request.filter_categories else None
        )
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lore/entities")
async def get_world_entities():
    try:
        results = lore_db.collection.get(include=["metadatas"])
        factions  = []
        resources = []
        wildlife  = []
        if results and results["ids"]:
            for idx, meta in enumerate(results["metadatas"]):
                cat   = str(meta.get("category", ""))
                title = str(meta.get("title", ""))
                entity = {"id": results["ids"][idx], "name": title, "title": title, "category": cat, "stats": {}}
                entity_file = ENTITIES_DIR / f"{title}.json"
                if entity_file.exists():
                    try:
                        with open(entity_file, "r", encoding="utf-8") as f:
                            entity["stats"] = json.load(f)
                    except Exception:
                        pass
                if "FACTION" in cat:
                    factions.append(entity)
                elif "RESOURCE" in cat:
                    resources.append(entity)
                elif "ANIMAL" in cat or "PLANT" in cat or "FAUNA" in cat or "FLORA" in cat:
                    wildlife.append(entity)
        return {
            "factions":  factions,
            "resources": resources,
            "wildlife":  wildlife,
            "total":     len(factions) + len(resources) + len(wildlife),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lore/config/save")
async def save_entity_config(payload: dict):
    try:
        entity_id   = payload.get("id", "Unknown_Entity")
        config_file = ENTITIES_DIR / f"{entity_id}_sim_config.json"
        ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
        existing = {}
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                try: existing = json.load(f)
                except Exception: pass
        existing.update(payload)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        return {"status": "success", "message": f"Saved sim config for {entity_id}", "path": str(config_file)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lore/generate_entities")
async def trigger_entity_generation():
    _kick_entity_generator()
    return {"status": "success", "message": "Entity generation launched in background."}

@app.post("/api/lore/import_map")
async def trigger_map_import(payload: dict):
    try:
        target_file = payload.get("filename")
        if not target_file:
            raise HTTPException(status_code=400, detail="Missing filename parameter")
        data_dir    = BASE_DIR / "data"
        filepath    = data_dir / target_file
        script_path = data_dir / "import_map.py"
        subprocess.Popen(
            [sys.executable, str(script_path), str(filepath)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"status": "success", "message": f"Map import started for {target_file}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    # ── Fetch faction seeds from local lore database if none provided ──────────────
    faction_seeds = req.faction_seeds or []
    if not faction_seeds:
        try:
            lore_data = await get_world_entities()
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
            print(f"[ARCHITECT] Loaded {len(faction_seeds)} factions from local Lore DB.")
        except Exception as e:
            print(f"[ARCHITECT] Warning: Could not fetch from local lore DB: {e}")

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
