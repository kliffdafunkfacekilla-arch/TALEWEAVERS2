from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import IngestRequest, IngestResponse, SearchRequest, SearchResponse
from core.vault_parser import parse_vault
from core.vector_store import LoreVaultDB
from collections import Counter
import uvicorn
import os
import json
import logging

app = FastAPI(title="S.A.G.A. Lore Vault API", description="Module 1: Lore Database")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)# Global DB instance
db = LoreVaultDB()

@app.post("/api/lore/ingest", response_model=IngestResponse)
async def ingest_lore(request: IngestRequest):
    """
    Ingests an Obsidian markdown vault, generates embeddings, and stores them in ChromaDB.
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
        
        # Statistics
        categories = [doc["category"] for doc in documents]
        category_counts = dict(Counter(categories))
        
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
    """
    Performs semantic search on the ingested lore documents.
    """
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
    so the React VTT can populate its World Builder editors.
    """
    try:
        # Get all documents in the DB
        results = db.collection.get(include=["metadatas"])
        
        factions = []
        resources = []
        wildlife = []
        
        if results and results["ids"]:
            for idx, meta in enumerate(results["metadatas"]):
                cat = str(meta.get("category", ""))
                title = str(meta.get("title", ""))
                
                entity = {"id": results["ids"][idx], "title": title, "category": cat}
                
                # Sort them into their buckets based on our LoreCategory Enums
                if "FACTION" in cat:
                    factions.append(entity)
                elif "RESOURCE" in cat:
                    resources.append(entity)
                elif "ANIMAL" in cat or "PLANT" in cat:
                    wildlife.append(entity)
                    
        return {
            "factions": factions,
            "resources": resources,
            "wildlife": wildlife
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lore/config/save")
async def save_entity_config(payload: dict):
    """
    Saves the God Engine parameters (Aggression, Diet, Rarity, etc.) for a specific Lore entity.
    This writes an override file that the C++ World Architect can parse during generation.
    """
    try:
        config_path = "../god_engine_overrides.json"
        
        # Load existing if available
        overrides = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    overrides = json.load(f)
                except:
                    pass
                    
        # Update the entity's specific configuration rules
        entity_id = payload.get("id", "Unknown_Entity")
        overrides[entity_id] = payload
        
        # Save back to disk
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=2)
            
        return {"status": "success", "message": f"Saved God Engine parameters for {entity_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "Lore Vault", "port": 8001}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
