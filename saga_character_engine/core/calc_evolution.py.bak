from .schemas import CoreAttributes, BiologicalEvolutions
from typing import List, Dict

# This would ideally be loaded from the JSON files in data/species_matrices/
# For now, we implement a mock registry based on the blueprint examples.
EVOLUTION_REGISTRY = {
    "skin_slot": {
        "Cactus Spines": {
            "stats": {"reflexes": 1, "awareness": 1},
            "passives": [
                {
                    "name": "Needle Burst",
                    "type": "Reaction",
                    "effect": "When hit by melee, explode spines. 5ft radius piercing dmg."
                }
            ]
        }
    },
    "body_slot": {
        "IronBark": {
            "stats": {"fortitude": 2},
            "passives": [
                {
                    "name": "Hardened Shell",
                    "type": "Passive",
                    "effect": "Reduce all incoming physical damage by 1."
                }
            ]
        }
    }
}

def apply_biology(base_stats: CoreAttributes, evolutions: BiologicalEvolutions) -> Dict:
    """
    Merges biological slot choices with base attributes and returns granted passives.
    """
    # Work on a copy of stats to avoid modifying the input directly if needed, 
    # but Pydantic models are passed by reference. Let's mutate it as per the request flow.
    granted_passives = []
    
    slots = [
        ("head_slot", evolutions.head_slot),
        ("body_slot", evolutions.body_slot),
        ("arms_slot", evolutions.arms_slot),
        ("legs_slot", evolutions.legs_slot),
        ("skin_slot", evolutions.skin_slot),
        ("special_slot", evolutions.special_slot),
    ]
    
    for slot_name, choice in slots:
        if slot_name in EVOLUTION_REGISTRY and choice in EVOLUTION_REGISTRY[slot_name]:
            data = EVOLUTION_REGISTRY[slot_name][choice]
            
            # Apply stat bonuses
            for stat, bonus in data.get("stats", {}).items():
                current_val = getattr(base_stats, stat)
                setattr(base_stats, stat, current_val + bonus)
            
            # Add passive skills
            granted_passives.extend(data.get("passives", []))
            
    return {
        "updated_stats": base_stats,
        "passives": granted_passives
    }
