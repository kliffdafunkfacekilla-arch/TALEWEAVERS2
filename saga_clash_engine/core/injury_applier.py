import random
from core.schemas import ClashResolution, ClashRequest

# A gritty list of visceral consequences for hitting 0 HP.
# The GM App's AI Narrator will read these and describe the gore natively.
BODY_TRAUMA_DB = [
    "1 Major Body Injury (Shattered Ribs)",
    "1 Major Body Injury (Severed Artery)",
    "1 Major Body Injury (Crushed Joint)",
    "1 Major Body Injury (Punctured Lung)",
    "1 Major Body Injury (Concussive Trauma)"
]

def apply_injuries(res: ClashResolution, req: ClashRequest) -> ClashResolution:
    """
    Intercepts the Clash damage and checks if either combatant dropped to 0 HP.
    If they do, it triggers the Dual-Track Trauma system.
    """
    # 1. Check Defender
    if res.defender_hp_change < 0:
        if req.defender.current_hp + res.defender_hp_change <= 0:
            res.defender_injury_applied = random.choice(BODY_TRAUMA_DB)

    # 2. Check Attacker (In case of a REVERSAL margin where the defender counters)
    if res.attacker_hp_change < 0:
        if req.attacker.current_hp + res.attacker_hp_change <= 0:
            res.attacker_injury_applied = random.choice(BODY_TRAUMA_DB)

    return res
