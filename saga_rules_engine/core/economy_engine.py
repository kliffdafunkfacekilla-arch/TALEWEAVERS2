import random

def calculate_d_dust_rate(base_rate: float = 10.0, chaos_level: int = 1) -> float:
    """
    Calculates the volatile D-Dust exchange rate based on world chaos.
    """
    # Chaos level increases volatility (e.g., Level 5 = 1.0 or 100% swing)
    volatility = chaos_level * 0.2 
    
    # Calculate the swing, but enforce a hard floor so prices never go negative
    min_swing = max(0.1, 1.0 - volatility)
    max_swing = 1.0 + volatility
    
    fluctuation = random.uniform(min_swing, max_swing)
    new_rate = base_rate * fluctuation
    
    return round(new_rate, 2)
