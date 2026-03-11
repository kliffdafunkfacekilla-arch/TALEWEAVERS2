import random
from .clash_schemas import ClashResolution, ClashRequest

# A gritty list of visceral consequences for hitting 0 HP.
# The Saga Director App's AI Narrator will read these and describe the gore natively.
BODY_TRAUMA_DB = [
    "1 Major Body Injury (Shattered Ribs)",
    "1 Major Body Injury (Severed Artery)",
    "1 Major Body Injury (Crushed Joint)",
    "1 Major Body Injury (Punctured Lung)",
    "1 Major Body Injury (Concussive Trauma)"
]

def apply_injuries(res: ClashResolution, req: ClashRequest) -> ClashResolution:
    """
    S.A.G.A. Injury Rules:
    - Any single blow dealing 5+ damage triggers an injury.
    - A CRITICAL_HIT (+10 margin) always triggers a MAJOR injury.
    - Dropping to 0 HP or less triggers an injury.
    """
    # 1. Check Defender
    dmg_to_def = abs(res.defender_hp_change)
    is_crit = res.clash_result == "CRITICAL_HIT"
    at_zero_def = (req.defender.current_hp + res.defender_hp_change) <= 0
    
    if dmg_to_def >= 5 or is_crit or at_zero_def:
        injury = random.choice(BODY_TRAUMA_DB)
        res.defender_injury_applied = f"MAJOR: {injury}" if is_crit else f"MINOR: {injury}"

    # 2. Check Attacker (Counter-damage/Reversals)
    dmg_to_atk = abs(res.attacker_hp_change)
    at_zero_atk = (req.attacker.current_hp + res.attacker_hp_change) <= 0
    if dmg_to_atk >= 5 or at_zero_atk:
        res.attacker_injury_applied = f"MINOR: {random.choice(BODY_TRAUMA_DB)}"

    return res
