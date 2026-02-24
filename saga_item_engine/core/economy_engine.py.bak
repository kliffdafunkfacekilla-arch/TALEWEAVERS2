import random

def calculate_d_dust_rate(base_rate: float = 10.0, chaos_level: int = 1) -> float:
    """
    Chaos level of the world increases the volatility of D-Dust.
    GM App pings this module when players enter a new town or wait 24 hours 
    to get the current D-Dust market value.
    """
    # Chaos level of the world increases the volatility of D-Dust
    volatility = chaos_level * 0.2 
    fluctuation = random.uniform(1.0 - volatility, 1.0 + volatility)
    
    new_rate = base_rate * fluctuation
    
    # Example: Base is 10 Aetherium. With high chaos, it might drop to 6 or spike to 14.
    return round(new_rate, 2)
