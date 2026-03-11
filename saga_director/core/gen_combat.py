import random
from typing import List
from .encounter_schemas import CombatEncounter, Combatant, SpatialData

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

def generate_tactical_grid(biome: str, difficulty: int, width: int = 15, height: int = 10) -> List[List[str]]:
    grid = [["EMPTY" for _ in range(width)] for _ in range(height)]
    
    # Obstacle frequency based on difficulty and biome
    obstacle_chance = 0.05 + (difficulty * 0.03)
    
    for r in range(height):
        for c in range(width):
            if random.random() < obstacle_chance:
                if biome == "Forest":
                    grid[r][c] = "TREE"
                elif biome == "Ruins" or biome == "Dungeon":
                    grid[r][c] = "WALL"
                elif biome == "Mountain":
                    grid[r][c] = "ROCK"
                    
            # Random Interactive Objects
            if random.random() < 0.03:
                grid[r][c] = random.choice(["BARREL", "CRATE", "TABLE", "CHEST"])
                
    return grid

def generate_hostile_threat(threat_level: int, seed: str = None, biome: str = "Forest") -> CombatEncounter:
    # ... (template selection)
    template = None
    if seed:
        for t in MONSTER_TEMPLATES:
            if t["name"].lower() in (seed or "").lower():
                template = t
                break
    
    if not template:
        if threat_level >= 4:
            template = MONSTER_TEMPLATES[2]
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
                x_offset=random.uniform(-10.0, 10.0),
                y_offset=random.uniform(-10.0, 10.0),
                footprint_radius=1.0
            )
        ))

    grid = generate_tactical_grid(biome, threat_level)

    return CombatEncounter(
        title=f"{template['name']} Ambush",
        narrative_prompt=f"Shadows detach themselves from the surroundings. {count} {template['name']}s are closing in!",
        enemies=enemies,
        terrain_difficulty=threat_level,
        escape_dc=10 + threat_level,
        grid=grid
    )
