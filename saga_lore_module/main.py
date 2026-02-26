from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.schemas import IngestRequest, IngestResponse, SearchRequest, SearchResponse
from core.vault_parser import parse_vault
from core.vector_store import LoreVaultDB
from collections import Counter
import uvicorn
import os

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "Lore Vault", "port": 8001}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
