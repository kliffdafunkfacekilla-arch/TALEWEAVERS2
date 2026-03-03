import random
from typing import Tuple, Optional

def resolve_volatility(dust_amount: int, chaos_level: int) -> Tuple[bool, Optional[str]]:
    """
    Checks if D-Dust usage triggers a magical misfire.
    Chaos Level acts as the threshold on a d12.
    """
    if dust_amount <= 0:
        return False, None
        
    roll = random.randint(1, 12)
    # Volatility increases with dust amount and chaos
    threshold = chaos_level + (dust_amount // 2)
    
    is_strike = roll <= threshold
    
    if is_strike:
        misfires = [
            "The D-Dust ignites prematurely! Your spell backfires with a surge of raw energy.",
            "Dimensional tremors ripple through your weave. The spell's focus shattered.",
            "A sudden void-leak drains your focus as the dust collapses into itself.",
            "The excess power causes your own magical aura to flicker and burn."
        ]
        return True, random.choice(misfires)
        
    return False, None
