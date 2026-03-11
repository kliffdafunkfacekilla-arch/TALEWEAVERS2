import random
from typing import Dict
from .encounter_schemas import HazardEncounter, SpatialData

# The 36 Tactical Triads are represented by combinations of Attribute Checks
# and Status Effects. This generator scales based on threat_level.

TRAP_TYPES = [
    {
        "name": "Spike Pit",
        "detection": "Awareness + Intuition",
        "disarm": "Logic + Finesse",
        "damage_base": "2d6",
        "damage_type": "Piercing",
        "injury": "Minor Leg"
    },
    {
        "name": "Aethel-Flare",
        "detection": "Knowledge + Willpower",
        "disarm": "Knowledge + Intuition",
        "damage_base": "1d10",
        "damage_type": "Aetheric",
        "injury": "Burned Mind"
    },
    {
        "name": "Crushing Block",
        "detection": "Awareness + Logic",
        "disarm": "Finesse + Logic",
        "damage_base": "3d6",
        "damage_type": "Blunt",
        "injury": "Crushed Torso"
    },
    {
        "name": "Toxic Spore Cloud",
        "detection": "Awareness + Knowledge",
        "disarm": "Endurance + Knowledge",
        "damage_base": "1d4",
        "damage_type": "Poison",
        "injury": "Infected Lungs"
    }
]

def generate_tactical_hazard(threat_level: int) -> HazardEncounter:
    base = random.choice(TRAP_TYPES)
    dc = 10 + (threat_level * 2) + random.randint(0, 4)
    
    return HazardEncounter(
        title=f"Lvl {threat_level} {base['name']}",
        narrative_prompt=f"A mechanical click echoes as you step on a pressure plate. A {base['name']} triggers!",
        detection_check={"triad": base["detection"], "dc": dc - 2},
        disarm_check={"triad": base["disarm"], "dc": dc},
        trigger_effect={
            "damage": f"{base['damage_base']} {base['damage_type']}",
            "save": f"{base['detection'].split(' + ')[-1]} Half",
            "injury": base["injury"]
        },
        spatial=SpatialData(
            x_offset=random.uniform(-5.0, 5.0),
            y_offset=random.uniform(-5.0, 5.0),
            footprint_radius=1.5
        )
    )
