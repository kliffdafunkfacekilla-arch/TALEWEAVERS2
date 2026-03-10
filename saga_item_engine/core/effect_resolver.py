import random
import re
from typing import Dict, Any

def parse_dice(dice_str: str) -> int:
    """
    Parses strings like '1d4', '2d6+2', or '1d8-1' and rolls the result.
    """
    # Regex captures: Group 1 (Count), Group 2 (Sides), Group 3 (Optional Math)
    match = re.search(r'(\d+)d(\d+)([\+\-]\d+)?', dice_str.lower().replace(" ", ""))
    if not match:
        return 0
    
    num_dice = int(match.group(1))
    dice_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if dice_sides < 1:
        return max(1, modifier)
    
    roll_total = sum(random.randint(1, dice_sides) for _ in range(num_dice))
    
    # Ensure a roll can't go below 1 after subtracting a modifier
    return max(1, roll_total + modifier)

def resolve_consumable(item_data: Dict[str, Any], target_vitals: Dict[str, Any]) -> Dict[str, Any]:
    """
    When a player uses a consumable, this module does the math.
    Strict isolation: Takes data, returns math result.
    """
    effect_type = item_data.get("effect_type", "NONE")
    effect_math = item_data.get("effect_math", "")
    item_name = item_data.get("name", "Unknown Item")
    
    result = {
        "item_name": item_name,
        "action": effect_type,
        "details": "",
        "math_result": 0,
        "target_pool": None,
        "is_unstable_triggered": False
    }

    # Handle instability
    if item_data.get("is_unstable", False):
        if random.randint(1, 20) == 1:
            result["is_unstable_triggered"] = True
            result["details"] = "UNSTABLE! The item exploded in your hands!"
            return result

    # Basic effect resolution
    if effect_type == "HEAL":
        # Example math: "Regain 1d4 Stamina"
        # We look for the dice pattern in the math string
        val = parse_dice(effect_math)
        result["math_result"] = val
        
        if "Stamina" in effect_math:
            result["target_pool"] = "Stamina"
        elif "Focus" in effect_math:
            result["target_pool"] = "Focus"
        elif "Health" in effect_math:
            result["target_pool"] = "Health"
            
        result["details"] = f"Recovered {val} {result['target_pool']}."

    elif effect_type == "DAMAGE":
        # Example math: "2d6 Fire Dmg 10ft radius"
        val = parse_dice(effect_math)
        result["math_result"] = val
        result["details"] = f"Dealt {val} damage. Resist save: {item_data.get('resist_save', 'None')}"

    elif effect_type == "BUFF":
        # Buffs are usually static or logic-heavy; returning the literal string or a simple flag
        result["details"] = f"Applied effect: {effect_math}"

    return result
