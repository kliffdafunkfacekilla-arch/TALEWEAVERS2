from .schemas import CoreAttributes, DerivedVitals

def calculate_pools(stats: CoreAttributes) -> DerivedVitals:
    """
    Strictly enforces the '6 and 6 split' math for survival pools.
    """
    max_hp = stats.might + stats.reflexes + stats.vitality
    max_stamina = stats.endurance + stats.fortitude + stats.finesse
    max_composure = stats.willpower + stats.logic + stats.awareness
    max_focus = stats.knowledge + stats.charm + stats.intuition
    
    return DerivedVitals(
        max_hp=max_hp,
        max_stamina=max_stamina,
        max_composure=max_composure,
        max_focus=max_focus
    )
