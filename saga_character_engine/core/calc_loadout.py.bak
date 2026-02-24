from .schemas import DerivedVitals
from typing import Dict

# Mock fee registry
LOADOUT_FEES = {
    "armor": {
        "Scale Mail": {"stamina": 2},
        "Plate Mail": {"stamina": 5},
        "Mystical Robes": {"focus": 3}
    },
    "weapon": {
        "Greatsword": {"stamina": 1},
        "Heavy Crossbow": {"stamina": 1}
    }
}

def apply_holding_fees(vitals: DerivedVitals, loadout: Dict[str, str]) -> Dict[str, int]:
    """
    Calculates the 'Holding Fees' based on equipped armor/weapons.
    Locks portions of Stamina or Focus.
    """
    fees = {"stamina": 0, "focus": 0}
    
    for category, item_name in loadout.items():
        if category in LOADOUT_FEES and item_name in LOADOUT_FEES[category]:
            item_fees = LOADOUT_FEES[category][item_name]
            for pool, amount in item_fees.items():
                fees[pool] += amount
                
    return fees
