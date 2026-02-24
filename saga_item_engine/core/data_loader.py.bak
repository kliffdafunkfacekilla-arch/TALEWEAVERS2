import json
import os
from typing import Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up an item by ID across all data files.
    """
    data_files = [
        "base_weapons.json",
        "base_armors.json",
        "hedge_charms.json"
    ]
    
    for filename in data_files:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r') as f:
            items = json.load(f)
            for item in items:
                if item.get("id") == item_id:
                    return item
    return None
