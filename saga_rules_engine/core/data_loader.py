import json
from pathlib import Path
from typing import Dict, Any, Optional

# Step up to the root project directory and find the master data folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def load_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up an item by ID strictly from the master Item_Builder.json.
    """
    filepath = DATA_DIR / "Item_Builder.json"
    
    if not filepath.exists():
        print(f"[WARNING] Master Item Database not found at {filepath}")
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            items = json.load(f)
            for item in items:
                if item.get("id") == item_id:
                    return item
    except Exception as e:
        print(f"[ERROR] Failed to parse Item_Builder.json: {e}")
        
    return None
