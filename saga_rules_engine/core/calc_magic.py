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
    Validates selected powers and calculates tactical stats:
    - Intensity = Governing Attribute // 3
    - Focus Cost = 2 (Base) + Tier
    - Aetherium Value = Tier * 50 (Resource cost for Item Foundry/Commerce)
    """
    if not selected_powers:
        return []
        
    if len(selected_powers) > 2:
        raise HTTPException(
            status_code=400, 
            detail=f"Character can only start with a maximum of 2 Tier 1 Spells. Received {len(selected_powers)}."
        )
        
    schools_db = load_schools_of_power()
    compiled_powers = []
    
    for power in selected_powers:
        spell_name = power.get("name")
        if not spell_name:
            continue
            
        # Find the school this spell belongs to
        target_school = None
        governing_attr = None
        spell_cost_str = "1"
        found_tier = "1"
        
        for attr, data in schools_db.items():
            for tier_num, tier_data in data.get("tiers", {}).items():
                for choice_type in ["OFFENSE", "DEFENSE", "UTILITY"]:
                    spell_info = tier_data.get(choice_type, {})
                    if spell_info.get("name") == spell_name:
                        target_school = data["school"]
                        governing_attr = attr.lower()
                        spell_cost_str = spell_info.get("cost", "1")
                        found_tier = tier_num
                        break
                if target_school: break
            if target_school: break
        
        if not target_school:
            raise HTTPException(status_code=400, detail=f"Spell '{spell_name}' not found in any known School of Power.")

        # Check Attribute Requirement (Base 12)
        attr_val = getattr(attributes, governing_attr, 0)
        if attr_val < 12:
            raise HTTPException(
                status_code=400,
                detail=f"Attribute '{governing_attr.upper()}' ({attr_val}) is too low to cast '{spell_name}'. Required: 12."
            )

        # Tactical Calculations
        import re
        tier = int(found_tier)
        intensity = attr_val // 3
        
        # Parse Focus/Stamina cost from string (e.g. "2 Stamina" -> 2)
        parsed_cost = 1
        num_match = re.search(r'\d+', spell_cost_str)
        if num_match:
            parsed_cost = int(num_match.group())

        aetherium_value = tier * 50

        compiled_powers.append({
            "name": spell_name,
            "school": target_school,
            "governing_attribute": governing_attr.upper(),
            "tier": str(tier),
            "intensity": intensity,
            "focus_cost": parsed_cost,
            "aetherium_value": aetherium_value,
            "description": f"A {target_school} power governed by {governing_attr.upper()}. Intensity {intensity}."
        })
            
    return compiled_powers
