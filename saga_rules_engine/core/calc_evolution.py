import json
import functools
from pathlib import Path
from .schemas import CoreAttributes, BiologicalEvolutions
from typing import List, Dict

# Safely point to the master data folder (root /data)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

@functools.lru_cache(maxsize=1)
def load_evolution_matrix() -> List[Dict]:
    """
    Loads the real Evolution_Matrix.json from the master database.
    NOTE: The result is cached. Do NOT mutate the returned list or its contents.
    """
    matrix_path = DATA_DIR / "Evolution_Matrix.json"
    if matrix_path.exists():
        with open(matrix_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_species_base() -> Dict[str, Dict[str, int]]:
    """Loads the Latin Square base stats for each species."""
    base_path = DATA_DIR / "species_base_stats.json"
    if base_path.exists():
        with open(base_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def apply_biology(evolutions: BiologicalEvolutions) -> Dict:
    """
    Initializes stats from species base and applies cumulative bonuses from choices.
    """
    granted_passives = []
    matrix_db = load_evolution_matrix()
    species_bases = load_species_base()
    
    # 1. Initialize from Latin Square Base
    # Normalizing species name for lookup
    species_key = evolutions.species_base.title()
    base_config = species_bases.get(species_key, {})
    
    final_stats = {
        "might": base_config.get("might", 10),
        "endurance": base_config.get("endurance", 10),
        "vitality": base_config.get("vitality", 10),
        "fortitude": base_config.get("fortitude", 10),
        "reflexes": base_config.get("reflexes", 10),
        "finesse": base_config.get("finesse", 10),
        "knowledge": base_config.get("knowledge", 10),
        "logic": base_config.get("logic", 10),
        "charm": base_config.get("charm", 10),
        "willpower": base_config.get("willpower", 10),
        "awareness": base_config.get("awareness", 10),
        "intuition": base_config.get("intuition", 10)
    }
    
    # 2. Map the schema slots to the player's choices
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
    
    stat_map = {
        "might": "might", "endurance": "endurance", "vitality": "vitality",
        "fortitude": "fortitude", "reflex": "reflexes", "reflexes": "reflexes", "finesse": "finesse",
        "knowledge": "knowledge", "logic": "logic", "charm": "charm",
        "willpower": "willpower", "awareness": "awareness", "intuition": "intuition"
    }

    # 3. Apply traits from the matrix
    for trait in matrix_db:
        trait_name = trait.get("name", "")
        if trait_name in chosen_traits and trait_name != "Standard":
            # Each biological trait gives stats defined in the matrix
            stats_config = trait.get("stats", {})
            for key, val in stats_config.items():
                # Handle single stat keys or comma-separated lists
                potential_stats = [s.strip().lower() for s in key.replace('+', '').split(',')]
                for ps in potential_stats:
                    import re
                    match = re.search(r'[a-zA-Z]+', ps)
                    if match:
                        clean_stat = stat_map.get(match.group(0))
                        if clean_stat and clean_stat in final_stats:
                            bonus = val if isinstance(val, int) else 1
                            final_stats[clean_stat] += bonus
            
            # Add passive abilities
            if "passives" in trait:
                granted_passives.extend(trait["passives"])
            elif "effect" in trait:
                granted_passives.append({
                    "name": trait_name,
                    "type": trait.get("type", "Biological Passive"),
                    "effect": trait["effect"]
                })
    
    return {
        "updated_stats": CoreAttributes(**final_stats),
        "passives": granted_passives
    }
