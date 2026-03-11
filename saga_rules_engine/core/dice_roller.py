import random

def roll_d20(is_advantage: bool = False, is_disadvantage: bool = False) -> tuple[int, int]:
    """
    Rolls 1d20 with Advantage or Disadvantage.
    Returns a tuple of (final_result, raw_die_face).
    """
    roll1 = random.randint(1, 20)
    
    if is_advantage:
        roll2 = random.randint(1, 20)
        final = max(roll1, roll2)
        # Note: In most systems, "raw die" for crit checks depends on the specific rule.
        # Here we'll take the 'final' result as the raw face for simplicity unless specified.
        return final, final
    
    if is_disadvantage:
        roll2 = random.randint(1, 20)
        final = min(roll1, roll2)
        return final, final
        
    return roll1, roll1

def roll_dice(dice_str: str) -> int:
    """
    Parses and rolls dice like "1d8+2" or "2d6".
    """
    try:
        if not dice_str:
            return 0
            
        parts = dice_str.lower().split('d')
        if len(parts) != 2:
            return int(dice_str) # Assume static value
            
        num_dice = int(parts[0])
        
        # Check for modifier
        bonus = 0
        if '+' in parts[1]:
            sides_part, bonus_part = parts[1].split('+')
            sides = int(sides_part)
            bonus = int(bonus_part)
        elif '-' in parts[1]:
            sides_part, bonus_part = parts[1].split('-')
            sides = int(sides_part)
            bonus = -int(bonus_part)
        else:
            sides = int(parts[1])
            
        total = sum(random.randint(1, sides) for _ in range(num_dice))
        return total + bonus
    except Exception:
        return 0
