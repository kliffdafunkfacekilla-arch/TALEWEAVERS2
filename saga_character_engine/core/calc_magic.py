import json
from pathlib import Path
from typing import List, Dict
from fastapi import HTTPException
from .schemas import CoreAttributes

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def load_schools_of_power() -> Dict:
    """Loads the 12 Schools of Power and their spell lists."""
    schools_path = DATA_DIR / "schools_of_power.json"
    if schools_path.exists():
        with open(schools_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"[WARNING] Could not find {schools_path}. Using empty schools.")
    return {}

def calculate_magic(attributes: CoreAttributes, selected_powers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Validates the selected powers based on the 12 Schools constraint:
    - User can choose max 2 Tier 1 spells.
    - User must have >= 12 in the corresponding attribute to unlock the school.
    """
    if not selected_powers:
        return []
        
    if len(selected_powers) > 2:
        raise HTTPException(
            status_code=400, 
            detail=f"Character can only start with a maximum of 2 Tier 1 Spells. Received {len(selected_powers)}."
        )
        
    schools_db = load_schools_of_power()
    
    # Pre-map available spells for checking
    valid_spells = {}
    for attr, data in schools_db.items():
        # Check if the player has >= 12 in the required stat
        attr_val = getattr(attributes, attr.lower(), 0)
        if attr_val >= 12:
            school_name = data["school"]
            for spell in data["spells"]:
                valid_spells[spell] = school_name
                
    compiled_powers = []
    
    for power in selected_powers:
        spell_name = power.get("name")
        if not spell_name:
            continue
            
        if spell_name in valid_spells:
            compiled_powers.append({
                "name": spell_name,
                "school": valid_spells[spell_name],
                "tier": "1"
            })
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Spell '{spell_name}' is either invalid, not a Tier 1 spell, or the character's Base Attribute is lower than 12 for its School."
            )
            
    return compiled_powers
