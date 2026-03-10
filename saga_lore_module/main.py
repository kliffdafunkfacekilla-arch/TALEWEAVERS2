from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import IngestRequest, IngestResponse, SearchRequest, SearchResponse
from core.vault_parser import parse_vault
from core.vector_store import LoreVaultDB
from collections import Counter
import uvicorn
import os
import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("saga_lore_module")

# ── Paths ─────────────────────────────────────────────────────────────────────
MODULE_DIR   = Path(__file__).resolve().parent
BASE_DIR     = MODULE_DIR.parent
OSTRAKA_DIR  = BASE_DIR / "data" / "Ostraka"
ENTITIES_DIR = BASE_DIR / "data" / "entities"

# ── State shared across requests ──────────────────────────────────────────────
_ingest_status = {
    "state":      "pending",   # pending | running | complete | error
    "docs_count": 0,
    "categories": {},
    "errors":     [],
    "entity_gen": "pending",   # pending | running | complete
}

# ── Global DB instance ────────────────────────────────────────────────────────
db = LoreVaultDB()


def _run_ingest_background():
    """
    Check if the ChromaDB collection is empty.
    If so, parse the Ostraka vault and ingest everything into ChromaDB,
    then kick off entity_generator.py as a background subprocess so the
    LLM can produce faction/fauna stat-block JSONs.
    """
    global _ingest_status
    try:
        current_count = db.collection.count()

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

        db.add_documents(documents)

        categories = [doc["category"] for doc in documents]
        category_counts = dict(Counter(categories))

        _ingest_status["state"]      = "complete"
        _ingest_status["docs_count"] = len(documents)
        _ingest_status["categories"] = category_counts
        logger.info(f"[LORE] Auto-ingest complete: {len(documents)} docs across {len(category_counts)} categories.")

        # Now kick off entity_generator.py in the background to produce stat-block JSONs
        _kick_entity_generator()

    except Exception as e:
        logger.error(f"[LORE] Auto-ingest failed: {e}")
        _ingest_status["state"]  = "error"
        _ingest_status["errors"] = [str(e)]


def _kick_entity_generator():
    """Spawn entity_generator.py as a background subprocess."""
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


# ── FastAPI lifespan (startup hook) ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: auto-ingest the Ostraka vault if ChromaDB is empty."""
    import threading
    thread = threading.Thread(target=_run_ingest_background, daemon=True)
    thread.start()
    yield
    # (shutdown logic goes here if needed)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="S.A.G.A. Lore Vault API",
    description="Module 1: Lore Database — auto-ingests Ostraka vault on first boot",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status":       "healthy",
        "module":       "Lore Vault",
        "port":         8001,
        "ingest_state": _ingest_status["state"],
        "docs_indexed": _ingest_status["docs_count"],
        "entity_gen":   _ingest_status["entity_gen"],
    }


@app.get("/api/lore/ingest_status")
async def ingest_status():
    """
    Returns the current ingest pipeline state.
    saga_architect polls this before calling /api/world/init to confirm
    faction data is ready.

    States:
      pending   — ingest not yet started
      running   — currently parsing & vectorising vault
      complete  — ChromaDB populated, entity_generator launched
      error     — something went wrong (check 'errors' field)
    """
    return {
        **_ingest_status,
        "vault_path":    str(OSTRAKA_DIR),
        "entities_path": str(ENTITIES_DIR),
        "chroma_count":  db.collection.count(),
    }


@app.post("/api/lore/ingest", response_model=IngestResponse)
async def ingest_lore(request: IngestRequest):
    """
    Manual ingest trigger — parses an Obsidian vault and stores embeddings in ChromaDB.
    Also kicks off entity_generator.py when done.
    """
    if request.force_rebuild:
        db.wipe_db()

    try:
        documents = parse_vault(request.vault_path)
        if not documents:
            return IngestResponse(
                status="warning",
                files_processed=0,
                categories_mapped={},
                errors=["No valid markdown files found in the specified path."]
            )

        db.add_documents(documents)
        categories = [doc["category"] for doc in documents]
        category_counts = dict(Counter(categories))

        _ingest_status["state"]      = "complete"
        _ingest_status["docs_count"] = len(documents)
        _ingest_status["categories"] = category_counts

        # Also fire entity generation
        _kick_entity_generator()

        return IngestResponse(
            status="success",
            files_processed=len(documents),
            categories_mapped=category_counts,
            errors=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/lore/search", response_model=SearchResponse)
async def search_lore(request: SearchRequest):
    """Performs semantic search on the ingested lore documents."""
    try:
        results = db.query(
            query_text=request.query,
            top_k=request.top_k,
            filter_categories=[str(c) for c in request.filter_categories] if request.filter_categories else None
        )
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lore/entities")
async def get_world_entities():
    """
    Fetches all categorized entities (Factions, Resources, Flora/Fauna)
    so the React VTT and saga_architect can populate faction seeds.

    Also enriches faction entries with stat-block JSON if entity_generator
    has produced output files in data/entities/.
    """
    try:
        results = db.collection.get(include=["metadatas"])
        factions  = []
        resources = []
        wildlife  = []

        if results and results["ids"]:
            for idx, meta in enumerate(results["metadatas"]):
                cat   = str(meta.get("category", ""))
                title = str(meta.get("title", ""))
                entity = {"id": results["ids"][idx], "name": title, "title": title, "category": cat, "stats": {}}

                # Try to enrich with generated stat-block JSON
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
    """
    Saves simulation parameters (Aggression, Diet, Rarity, etc.) for a lore entity.
    Now writes to data/entities/<name>_sim_config.json rather than the old god_engine_overrides.
    """
    try:
        entity_id   = payload.get("id", "Unknown_Entity")
        config_file = ENTITIES_DIR / f"{entity_id}_sim_config.json"
        ENTITIES_DIR.mkdir(parents=True, exist_ok=True)

        # Merge with existing config if present
        existing = {}
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except Exception:
                    pass

        existing.update(payload)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        return {"status": "success", "message": f"Saved sim config for {entity_id}", "path": str(config_file)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/lore/generate_entities")
async def trigger_entity_generation():
    """Manual trigger to re-run entity_generator.py in the background."""
    _kick_entity_generator()
    return {"status": "success", "message": "Entity generation launched in background."}


@app.post("/api/lore/import_map")
async def trigger_map_import(payload: dict):
    """Trigger the map import script in the background."""
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
