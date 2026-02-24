from core.schemas import ClashResolution


# Dual-Track Injury thresholds
# If a combatant hits 0 HP, they're incapacitated. 
# The injury applier converts hp_change values into descriptive injury slots.

_MINOR_THRESHOLD = -5
_MODERATE_THRESHOLD = -10
_SEVERE_THRESHOLD = -15


def apply_injuries(resolution: ClashResolution) -> ClashResolution:
    """
    Post-clash injury assessment.
    
    If a character drops to 0 HP during the Clash, this script intercepts the
    result and translates raw HP numbers into Dual-Track Injury slots for the
    GM App to display.

    Injury levels:
        0 to -4   → "Minor Injury"
        -5 to -9  → "Moderate Injury"
        -10 to -14 → "Severe Injury"
        -15+      → "Critical Injury — possibly incapacitated"
    """
    if resolution.defender_hp_change < 0:
        resolution.defender_injury_applied = _classify_injury(resolution.defender_hp_change)

    if resolution.attacker_hp_change < 0:
        resolution.attacker_injury_applied = _classify_injury(resolution.attacker_hp_change)

    return resolution


def _classify_injury(hp_change: int) -> str:
    if hp_change >= _MINOR_THRESHOLD:
        return "Minor Injury"
    elif hp_change >= _MODERATE_THRESHOLD:
        return "Moderate Injury"
    elif hp_change >= _SEVERE_THRESHOLD:
        return "Severe Injury"
    else:
        return "Critical Injury — combatant possibly incapacitated"
