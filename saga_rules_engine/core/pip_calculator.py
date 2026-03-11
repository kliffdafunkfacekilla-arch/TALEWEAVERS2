from typing import Optional


def check_for_pips(
    raw_die: int,
    is_success: bool,
    is_life_or_death: bool
) -> Optional[str]:
    """
    The "Scars & Stars" progression system.
    Checks a raw die result against the three pip trigger conditions.

    Returns:
        "STAR"     - Nat 20: Perfection under fire.
        "SCAR"     - Nat 1: Disastrous failure, painful lesson learned.
        "SURVIVOR" - A success on a life-or-death check (Director-flagged). MVP moment.
        None       - Routine checks yield no pip progression.

    Priority: Nat 20 is always a STAR. Nat 1 is always a SCAR.
    SURVIVOR only triggers on a normal (non-Nat) success when is_life_or_death is True.
    """
    if raw_die == 20:
        return "STAR"

    if raw_die == 1:
        return "SCAR"

    if is_success and is_life_or_death:
        return "SURVIVOR"

    return None
