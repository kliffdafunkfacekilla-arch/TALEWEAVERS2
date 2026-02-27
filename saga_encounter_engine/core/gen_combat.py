import random
from .schemas import CombatEncounter, Combatant, SpatialData

# Combatant templates that scale with threat level
MONSTER_TEMPLATES = [
    {
        "name": "Wolf Cultist",
        "rank": "Mook",
        "hp_base": 12,
        "stamina_base": 6,
        "traits": ["Aggressive", "Pack Tactics"],
        "weapons": ["Curved Dagger"],
        "armor_base": 1
    },
    {
        "name": "Eldritch Skitterer",
        "rank": "Mook",
        "hp_base": 8,
        "stamina_base": 10,
        "traits": ["Fast", "Poisonous"],
        "weapons": ["Chitinous Claws"],
        "armor_base": 0
    },
    {
        "name": "Bone-Grit Marauder",
        "rank": "Elite",
        "hp_base": 25,
        "stamina_base": 15,
        "traits": ["Tough", "Brutal"],
        "weapons": ["Heavy Maul"],
        "armor_base": 3
    }
]

def generate_hostile_threat(threat_level: int, seed: str = None) -> CombatEncounter:
    # If seed mentions a specific name, try to match it
    template = None
    if seed:
        for t in MONSTER_TEMPLATES:
            if t["name"].lower() in seed.lower():
                template = t
                break
    
    if not template:
        # Pick based on threat level
        if threat_level >= 4:
            template = MONSTER_TEMPLATES[2] # Marauder
        else:
            template = random.choice(MONSTER_TEMPLATES[:2])

    count = random.randint(1 + (threat_level // 2), 2 + threat_level)
    enemies = []
    
    for i in range(count):
        enemies.append(Combatant(
            name=f"{template['name']} {i+1}",
            rank=template["rank"],
            hp=template["hp_base"] + (threat_level * 2),
            stamina=template["stamina_base"] + threat_level,
            traits=template["traits"],
            weapons=template["weapons"],
            armor=template["armor_base"] + (threat_level // 2),
            spatial=SpatialData(
                x_offset=random.uniform(-15.0, 15.0),
                y_offset=random.uniform(-15.0, 15.0),
                footprint_radius=1.0
            )
        ))

    return CombatEncounter(
        title=f"{template['name']} Ambush",
        narrative_prompt=f"Shadows detach themselves from the surroundings. {count} {template['name']}s are closing in!",
        enemies=enemies,
        terrain_difficulty=threat_level,
        escape_dc=10 + threat_level
    )
