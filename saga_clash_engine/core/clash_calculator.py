import random
from core.schemas import ClashRequest, ClashResolution


def roll_d20() -> int:
    return random.randint(1, 20)


def roll_dice(dice_str: str) -> int:
    """
    Parses and rolls dice like '1d8+2' or '2d6'.
    Returns 0 if the string is empty or unparseable.
    """
    try:
        if not dice_str:
            return 0
        parts = dice_str.lower().split('d')
        if len(parts) != 2:
            return int(dice_str)
        num_dice = int(parts[0])
        bonus = 0
        if '+' in parts[1]:
            sides_part, bonus_part = parts[1].split('+')
            bonus = int(bonus_part)
        elif '-' in parts[1]:
            sides_part, bonus_part = parts[1].split('-')
            bonus = -int(bonus_part)
        else:
            sides_part = parts[1]
        sides = int(sides_part.strip())
        total = sum(random.randint(1, sides) for _ in range(num_dice))
        return total + bonus
    except Exception:
        return 0


def resolve_clash(req: ClashRequest) -> ClashResolution:
    """
    The Margin-of-Victory calculator.

    Step 1: Roll 1d20 for both sides and add their burned Stamina and pool.
    Step 2: Compare. margin = atk_total - def_total.
    Step 3: Determine outcome from the margin.

    ─────────────────────────────────────────────────────────────────────
    | margin >= 5   → CRUSHING_WIN  | Full weapon damage + chaos effect │
    | 1 <= margin <= 4 → SCRAPE     | Half weapon damage                │
    | margin < 0    → REVERSAL      | Defender deals 2 chip damage      │
    | margin == 0   → DEADLOCK      | No damage; chaos may trigger      │
    ─────────────────────────────────────────────────────────────────────
    """
    # Step 1: Roll for both sides and add pools + burned stamina
    atk_roll = roll_d20()
    def_roll = roll_d20()

    atk_total = atk_roll + req.attacker.attack_or_defense_pool + req.attacker.stamina_burned
    def_total = def_roll + req.defender.attack_or_defense_pool + req.defender.stamina_burned

    margin = atk_total - def_total

    res = ClashResolution(
        clash_result="DEADLOCK",    # Default, will be overwritten
        attacker_roll=atk_total,
        defender_roll=def_total,
        margin=margin,
        stamina_deducted_attacker=req.attacker.stamina_burned,
        stamina_deducted_defender=req.defender.stamina_burned,
    )

    # Step 2: Determine outcome based on the Margin
    if margin >= 5:
        # CRUSHING WIN — roll full weapon damage
        res.clash_result = "CRUSHING_WIN"
        damage = roll_dice(req.attacker.weapon_damage_dice) if req.attacker.weapon_damage_dice else 1
        res.defender_hp_change = -damage

    elif 1 <= margin <= 4:
        # SCRAPE — half damage, no tactical advantage
        res.clash_result = "SCRAPE"
        damage = roll_dice(req.attacker.weapon_damage_dice) if req.attacker.weapon_damage_dice else 1
        res.defender_hp_change = -(max(1, damage // 2))

    elif margin < 0:
        # REVERSAL — defender wins; attacker takes chip damage
        res.clash_result = "REVERSAL"
        res.attacker_hp_change = -2   # Chip damage

    else:
        # DEADLOCK — margin == 0; both locked, no damage
        res.clash_result = "DEADLOCK"
        # In high chaos, the world reacts
        if req.chaos_level > 3:
            res.chaos_effect_triggered = "Reality Warp: Ground shifts, both fall Prone."

    return res
