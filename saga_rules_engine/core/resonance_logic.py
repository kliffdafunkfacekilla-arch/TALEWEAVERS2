from typing import Dict

# Mapping of Schools to their favored and hindered environments
# Schools: NEXUS, MASS, MOTUS, FLUX, VITA, LEX, RATIO, ORDO, LUX, OMEN, AURA, ANUMIS

RESONANCE_MATRIX = {
    "VITA": {
        "favored_biomes": ["Jungle", "Forest", "Swamp"],
        "hindered_biomes": ["Wasteland", "Tundra"],
        "favored_weather": ["Heavy Rain"],
    },
    "LUX": {
        "favored_biomes": ["Plains", "Desert"],
        "hindered_biomes": ["Cave", "Deep Forest"],
        "favored_weather": ["Clear Skies"],
        "hindered_weather": ["Toxic Fog", "Overcast"]
    },
    "IGNIS": { # Purely conceptual/flavor mapping if needed
        "favored_biomes": ["Desert", "Volcanic"],
        "hindered_biomes": ["Tundra", "Ocean"],
    },
    "ANUMIS": {
        "favored_biomes": ["Graveyard", "Ruins"],
        "favored_weather": ["Toxic Fog"]
    }
}

def calculate_resonance(school: str, biome: str, weather: str) -> tuple[int, str]:
    res = RESONANCE_MATRIX.get(school.upper(), {})
    bonus = 0
    flavor = ""
    
    if biome in res.get("favored_biomes", []):
        bonus += 1
        flavor = f"The {biome} environment resonates with your {school} essence."
    elif biome in res.get("hindered_biomes", []):
        bonus -= 1
        flavor = f"The {biome} air feels heavy and resistant to your {school} weave."
        
    if weather in res.get("favored_weather", []):
        bonus += 1
        flavor += f" The {weather} acts as a conduit for your power."
    elif weather in res.get("hindered_weather", []):
        bonus -= 1
        flavor += f" The {weather} dampens your magical focus."
        
    if bonus == 0:
        flavor = "The weave is stable in this environment."
        
    return bonus, flavor
