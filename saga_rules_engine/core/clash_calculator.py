import random
from .clash_schemas import ClashRequest, ClashResolution, CombatantState


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
    S.A.G.A. Realignment: 
    1d20 + Skill Rank + Stat Mod + (Rank // 2)
    
    Thresholds:
    10+   : Critical (2x Dmg)
    4 - 9 : Normal Dmg
    1 - 3 : Graze (Minor Composure Stress)
    0     : CLASH (Tie)
    -1 to -5 : Defense Success
    -6 to -11: Rattling Defense (Attacker takes Composure Stress)
    -11+  : Critical Miss (Prone)
    """
    # --- Roll with Adv/Dis ---
    def roll_with_benefit(base_roll_func, advantage: bool, disadvantage: bool):
        if advantage and not disadvantage:
            return max(base_roll_func(), base_roll_func())
        if disadvantage and not advantage:
            return min(base_roll_func(), base_roll_func())
        return base_roll_func()

    atk_roll = roll_with_benefit(roll_d20, req.attacker_advantage, req.attacker_disadvantage)
    def_roll = roll_with_benefit(roll_d20, req.defender_advantage, req.defender_disadvantage)

    # Formula: d20 + Skill + Stat + (Rank // 2) tier bonus
    atk_bonus = req.attacker.skill_rank + req.attacker.stat_mod + (req.attacker.skill_rank // 2)
    def_bonus = req.defender.skill_rank + req.defender.stat_mod + (req.defender.skill_rank // 2)

    atk_total = atk_roll + atk_bonus
    def_total = def_roll + def_bonus

    margin = atk_total - def_total

    res = ClashResolution(
        clash_result="DEADLOCK",
        attacker_roll=atk_total,
        defender_roll=def_total,
        margin=margin,
        stamina_deducted_attacker=req.attacker.stamina_burned,
        stamina_deducted_defender=req.defender.stamina_burned,
    )

    damage = roll_dice(req.attacker.weapon_damage_dice) if req.attacker.weapon_damage_dice else 1

    if margin >= 10:
        res.clash_result = "CRITICAL_HIT"
        res.defender_hp_change = -(damage * 2)
    elif 4 <= margin <= 9:
        res.clash_result = "NORMAL_HIT"
        res.defender_hp_change = -damage
    elif 1 <= margin <= 3:
        res.clash_result = "GRAZE"
        res.defender_composure_change = -1 # Minor stress
    elif margin == 0:
        res.clash_result = "CLASH_TIE"
    elif -5 <= margin <= -1:
        res.clash_result = "DEFENSIVE_SUCCESS"
    elif -11 <= margin <= -6:
        res.clash_result = "RATTLING_DEFENSE"
        res.attacker_composure_change = -1 # Attacker takes stress
    elif margin < -11:
        res.clash_result = "CRITICAL_MISS"
        res.chaos_effect_triggered = "Attacker falls PRONE."

    return res
