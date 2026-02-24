import json
from pathlib import Path
from .schemas import CoreAttributes, BiologicalEvolutions
from typing import List, Dict

# Safely point to the master data folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def load_evolution_matrix() -> List[Dict]:
    """Loads the real Evolution_Matrix.json from the master database."""
    matrix_path = DATA_DIR / "Evolution_Matrix.json"
    if matrix_path.exists():
        with open(matrix_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"[WARNING] Could not find {matrix_path}. Using empty matrix.")
    return []

def apply_biology(base_stats: CoreAttributes, evolutions: BiologicalEvolutions) -> Dict:
    """
    Scans the actual Evolution Matrix for the player's 6 chosen slots,
    merges the biological stats with base attributes, and grants passives.
    """
    granted_passives = []
    matrix_db = load_evolution_matrix()
    
    # Map the schema slots to the player's choices
    chosen_traits = [
        evolutions.head_slot,
        evolutions.body_slot,
        evolutions.arms_slot,
        evolutions.legs_slot,
        evolutions.skin_slot,
        evolutions.special_slot,
    ]
    
    # Loop through the database. If a trait matches a player's choice, apply it.
    for trait in matrix_db:
        trait_name = trait.get("name", "")
        
        if trait_name in chosen_traits and trait_name != "Standard":
            # 1. Apply stat bonuses (e.g., {"fortitude": 2})
            for stat, bonus in trait.get("stats", {}).items():
                if hasattr(base_stats, stat):
                    current_val = getattr(base_stats, stat)
                    setattr(base_stats, stat, current_val + bonus)
            
            # 2. Add passive skills or abilities linked to this evolution
            if "passives" in trait:
                granted_passives.extend(trait["passives"])
            elif "effect" in trait:
                # Fallback if the JSON uses flat effects instead of lists
                granted_passives.append({
                    "name": trait_name,
                    "type": trait.get("type", "Biological Passive"),
                    "effect": trait["effect"]
                })
            
    return {
        "updated_stats": base_stats,
        "passives": granted_passives
    }
