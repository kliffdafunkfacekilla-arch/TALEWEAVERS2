import random
import uuid
from fastapi import FastAPI, Query
from typing import List, Optional

# Changed to direct import for easier standalone execution
try:
    from schemas import (
        EncounterType, CombatEncounter, SocialEncounter, HazardEncounter,
        PuzzleEncounter, DiscoveryEncounter, DilemmaEncounter, Encounter, Choice
    )
except ImportError:
    from .schemas import (
        EncounterType, CombatEncounter, SocialEncounter, HazardEncounter,
        PuzzleEncounter, DiscoveryEncounter, DilemmaEncounter, Encounter, Choice
    )

app = FastAPI(title="TALEWEAVERS Encounter & Obstacle Engine")

# Mock data for generation
ENEMIES = {
    "Forest": ["Goblin Scout", "Giant Spider", "Dire Wolf", "Owlbear"],
    "Dungeon": ["Skeleton", "Zombie", "Orc Warrior", "Dark Cultist"],
    "Urban": ["Street Thug", "Pickpocket", "Corrupt Guard", "Assassin"],
    "Desert": ["Sand Raider", "Scorpion", "Mummy", "Fire Elemental"]
}

NPCS = ["Traveling Merchant", "Wounded Soldier", "Hermit Sage", "Excited Bard"]

HAZARDS = {
    "Forest": ["Hidden Pit Trap", "Poisonous Brambles", "Falling Tree"],
    "Dungeon": ["Spike Trap", "Acid Pool", "Collapsing Ceiling"],
    "Urban": ["Loose Roof Tiles", "Sewer Gas", "Crowded Stampede"],
    "Desert": ["Quick Sand", "Heat Mirage", "Dust Storm"]
}

PUZZLES = ["Riddle of the Sphinx", "Ancient Gear Mechanism", "Color-Coded Orbs", "Sun-Tracking Mirror"]

LORE_SNIPPETS = [
    "A rusted plaque speaks of an empire lost to time.",
    "Faded murals depict a war between gods and mortals.",
    "A diary entry mentions a treasure hidden 'where the sun never shines'."
]

@app.get("/generate-encounter", response_model=Encounter)
async def generate_encounter(
    biome: str = Query(..., description="The biome where the encounter occurs"),
    threat_level: int = Query(..., ge=1, le=10, description="Threat level from 1 to 10")
):
    # Determine encounter type randomly
    encounter_type = random.choice(list(EncounterType))
    
    encounter_id = str(uuid.uuid4())[:8]
    
    if encounter_type == EncounterType.COMBAT:
        biome_enemies = ENEMIES.get(biome, ENEMIES["Forest"])
        num_enemies = random.randint(1, threat_level + 1)
        enemies = [{"name": random.choice(biome_enemies), "level": threat_level} for _ in range(num_enemies)]
        
        return CombatEncounter(
            id=encounter_id,
            name=f"Ambush in the {biome}",
            description=f"A group of hostile entities has spotted you.",
            threat_level=threat_level,
            enemies=enemies
        )
    
    elif encounter_type == EncounterType.SOCIAL:
        npc = random.choice(NPCS)
        return SocialEncounter(
            id=encounter_id,
            name=f"Meeting with {npc}",
            description=f"You encounter a {npc} who seems to have something to say.",
            threat_level=threat_level,
            target_npc=npc,
            composure=threat_level * 2,
            social_stakes="Information regarding the local area"
        )
    
    elif encounter_type == EncounterType.HAZARD:
        biome_hazards = HAZARDS.get(biome, HAZARDS["Forest"])
        hazard = random.choice(biome_hazards)
        return HazardEncounter(
            id=encounter_id,
            name=hazard,
            description=f"The environment itself poses a threat: {hazard}.",
            threat_level=threat_level,
            hazard_type="Environmental",
            bypass_condition="Requires a successful Agility or Perception check",
            damage_type="Physical / Elemental"
        )
    
    elif encounter_type == EncounterType.PUZZLE:
        puzzle = random.choice(PUZZLES)
        return PuzzleEncounter(
            id=encounter_id,
            name=puzzle,
            description=f"A {puzzle} blocks your path.",
            threat_level=threat_level,
            mechanism="Magic / Mechanical",
            difficulty_class=10 + threat_level,
            reward_hint="A small hidden compartment or passage"
        )
    
    elif encounter_type == EncounterType.DISCOVERY:
        return DiscoveryEncounter(
            id=encounter_id,
            name="Ancient Remains",
            description="You find something of interest in the wreckage.",
            threat_level=threat_level,
            lore_snippet=random.choice(LORE_SNIPPETS),
            hidden_item_id=f"ITEM_{random.randint(100, 999)}"
        )
    
    elif encounter_type == EncounterType.DILEMMA:
        return DilemmaEncounter(
            id=encounter_id,
            name="Difficult Choice",
            description="You are faced with a moral or tactical dilemma.",
            threat_level=threat_level,
            choices=[
                Choice(
                    choice="Help the desperate soul",
                    cost={"stamina": 10},
                    reward={"reputation": 5}
                ),
                Choice(
                    choice="Keep moving and ignore them",
                    cost={},
                    reward={"time_saved": "Moderate"}
                )
            ]
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
