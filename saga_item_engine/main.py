from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.economy_engine import calculate_d_dust_rate
from core.effect_resolver import resolve_consumable
from core.data_loader import load_item_by_id

app = FastAPI(title="T.A.L.E.W.E.A.V.E.R. Item Foundry", version="1.0.0")

class EconomyRequest(BaseModel):
    base_rate: float = 10.0
    chaos_level: int = 1

class ResolveRequest(BaseModel):
    item_id: str
    target_vitals: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "Item Foundry", "port": 8005}

@app.post("/economy/rate")
async def get_economy_rate(request: EconomyRequest):
    """
    Returns the current D-Dust to Aetherium exchange rate.
    """
    rate = calculate_d_dust_rate(request.base_rate, request.chaos_level)
    return {"exchange_rate": rate, "unit": "1g D-Dust = X Aetherium"}

@app.post("/items/resolve")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
