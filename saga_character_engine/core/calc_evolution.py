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
        evolutions.size_slot,
        evolutions.ancestry_slot,
        evolutions.head_slot,
        evolutions.body_slot,
        evolutions.arms_slot,
        evolutions.legs_slot,
        evolutions.skin_slot,
        evolutions.special_slot,
    ]
    
    # Build a lookup for easier matching
    stat_map = {
        "might": "might", "endurance": "endurance", "vitality": "vitality",
        "fortitude": "fortitude", "reflex": "reflexes", "reflexes": "reflexes", "finesse": "finesse",
        "knowledge": "knowledge", "logic": "logic", "charm": "charm",
        "willpower": "willpower", "awareness": "awareness", "intuition": "intuition"
    }

    # Loop through the database. If a trait matches a player's choice, apply it.
    for trait in matrix_db:
        trait_name = trait.get("name", "")
        
        if trait_name in chosen_traits and trait_name != "Standard":
            # 1. Apply stat bonuses
            # Format could be {"fortitude": 2} or {"+2 reflex, +1 finesse": 1}
            for stat_key, bonus_val in trait.get("stats", {}).items():
                # Handle old format {"fortitude": 2}
                if stat_key in stat_map:
                    mapped_stat = stat_map[stat_key]
                    if hasattr(base_stats, mapped_stat):
                        current_val = getattr(base_stats, mapped_stat)
                        setattr(base_stats, mapped_stat, current_val + bonus_val)
                # Handle string format like "+2 reflex, +1 finesse"
                elif "," in stat_key or "+" in stat_key or "-" in stat_key:
                    import re
                    # Find and parse all '+1 stat' or '-2 stat'
                    matches = re.finditer(r'([+-]?\s*\d+)\s*([a-zA-Z]+)', stat_key)
                    for match in matches:
                        try:
                            num = int(match.group(1).replace(' ', ''))
                            stat_name = match.group(2).lower()
                            if stat_name in stat_map:
                                mapped_stat = stat_map[stat_name]
                                if hasattr(base_stats, mapped_stat):
                                    current_val = getattr(base_stats, mapped_stat)
                                    setattr(base_stats, mapped_stat, current_val + num * bonus_val)
                        except ValueError:
                            pass
            
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
