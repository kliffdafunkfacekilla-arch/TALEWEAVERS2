import json
from pathlib import Path
from .schemas import DerivedVitals
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def load_items_db() -> List[Dict]:
    """Loads the real Item_Builder.json to check weapon and armor weights."""
    item_path = DATA_DIR / "Item_Builder.json"
    if item_path.exists():
        with open(item_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def apply_holding_fees(vitals: DerivedVitals, loadout: Dict[str, str]) -> Dict[str, int]:
    """
    Calculates the 'Holding Fees' based on equipped armor/weapons.
    Locks portions of Stamina or Focus by matching equipped items to the DB.
    """
    fees = {"stamina": 0, "focus": 0}
    items_db = load_items_db()
    
    # Extract just the names of the items the player has equipped
    equipped_item_names = list(loadout.values())
    
    for item in items_db:
        if item.get("name") in equipped_item_names:
            # Check if the item has specific lock fees
            item_fees = item.get("holding_fees", {})
            
            # If "holding_fees" isn't strictly defined, fallback to looking for 'stamina_lock'
            if "stamina_lock" in item:
                fees["stamina"] += item["stamina_lock"]
            if "focus_lock" in item:
                fees["focus"] += item["focus_lock"]
                
            # Add explicit fees
            for pool, amount in item_fees.items():
                if pool in fees:
                    fees[pool] += amount
                
    return fees
