import json
import random
import uuid
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ==========================================
# FILE LOADING LOGIC (The Real Data)
# ==========================================
# This safely navigates up one folder to find your master 'data' directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_game_data(filename: str):
    """Safely loads a JSON file from the master data folder."""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        print(f"[WARNING] Missing database file: {file_path}")
        return [] # Return empty list if the file hasn't been built yet
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load the databases into memory when the server boots
ENEMY_DB = load_game_data("Enemy_Builder.json")
# You can create these JSON files later to expand the other encounter types!
QUEST_DB = load_game_data("Quest_Templates.json") 
ITEM_DB = load_game_data("Item_Builder.json")

# ==========================================
# THE ENGINE ROUTER
# ==========================================

def generate_terrain_grid(biome: str, width: int = 15, height: int = 10):
    """Generates a 2D array of tile types based on biome."""
    grid = []
    
    # Biome-specific obstacle chances
    weights = {
        "Forest": {"TREE": 0.25, "ROCK": 0.05, "MUD": 0.1},
        "Tundra": {"SNOW": 0.4, "ROCK": 0.1, "ICE": 0.05},
        "Desert": {"SAND_DUNES": 0.2, "ROCK": 0.1},
        "Swamp": {"WATER": 0.3, "MUD": 0.2, "TREE": 0.1},
        "Mountains": {"ROCK": 0.4, "FALLEN_STORES": 0.1}
    }
    
    biome_weights = weights.get(biome, {"ROCK": 0.05})
    
    for row in range(height):
        grid_row = []
        for col in range(width):
            roll = random.random()
            tile = "EMPTY"
            
            cumulative = 0
            for type_name, chance in biome_weights.items():
                cumulative += chance
                if roll < cumulative:
                    tile = type_name
                    break
            
            grid_row.append(tile)
        grid.append(grid_row)
        
    return grid

@app.get("/generate-encounter", response_model=Encounter)
async def generate_encounter(
    biome: str = Query(..., description="The biome where the encounter occurs, e.g., 'Tundra', 'Forest'"),
    threat_level: int = Query(..., ge=1, le=10, description="Threat level from 1 to 10")
):
    # Roll the procedural dice for the encounter type
    encounter_type = random.choice(list(EncounterType))
    encounter_id = f"ENC_{str(uuid.uuid4())[:8].upper()}"
    
    # Generate the tactical grid
    tactical_grid = generate_terrain_grid(biome)
    
    # ---------------------------------------------------------
    # 1. COMBAT (Now wired to your actual Enemy_Builder.json)
    # ---------------------------------------------------------
    if encounter_type == EncounterType.COMBAT:
        if not ENEMY_DB:
            raise HTTPException(status_code=500, detail="Enemy_Builder.json is missing or empty.")

        # Filter real enemies by checking if the requested biome is in their string/list
        # (This handles both formats: "biomes": "Forest, Swamp" OR "biomes": ["Forest", "Swamp"])
        valid_enemies = []
        for enemy in ENEMY_DB:
            # Assuming your JSON has a "biomes", "habitat", or "tags" field
            tags = str(enemy.get("biomes", "")) + str(enemy.get("habitat", "")) + str(enemy.get("tags", ""))
            if biome.lower() in tags.lower():
                valid_enemies.append(enemy)

        # Fallback if no enemies match the biome exactly
        if not valid_enemies:
            valid_enemies = ENEMY_DB 

        # Generate the combat squad
        num_enemies = random.randint(1, max(1, threat_level // 2))
        squad = []
        for _ in range(num_enemies):
            chosen = random.choice(valid_enemies)
            squad.append({
                "name": chosen.get("name", "Unknown Entity"),
                "level": chosen.get("level", threat_level),
                "hp": chosen.get("base_hp", 10),
                "stats": chosen.get("stats", {})
            })
        
        return CombatEncounter(
            id=encounter_id,
            name=f"Hostile Contact in the {biome}",
            description=f"You have been ambushed by a squad of {squad[0]['name']}s.",
            threat_level=threat_level,
            enemies=squad,
            grid=tactical_grid
        )
    
    # ---------------------------------------------------------
    # 2. SOCIAL (Currently using generic placeholders until NPC_Builder is made)
    # ---------------------------------------------------------
    elif encounter_type == EncounterType.SOCIAL:
        # FUTURE UPGRADE: ENEMY_DB = load_game_data("NPC_Builder.json")
        return SocialEncounter(
            id=encounter_id,
            name="Wandering Traveler",
            description="You spot a figure resting off the side of the path.",
            threat_level=threat_level,
            target_npc="Suspicious Scavenger",
            composure=threat_level * 3,
            social_stakes="They are hoarding D-Dust and Aetherium.",
            grid=tactical_grid
        )
    
    # ---------------------------------------------------------
    # 3. HAZARD (Traps & Environments)
    # ---------------------------------------------------------
    elif encounter_type == EncounterType.HAZARD:
        return HazardEncounter(
            id=encounter_id,
            name=f"{biome} Environmental Anomaly",
            description=f"The {biome} itself turns against you. Proceed with caution.",
            threat_level=threat_level,
            hazard_type="Terrain/Weather",
            bypass_condition="Requires Mobility or Awareness check.",
            damage_type="True Damage",
            grid=tactical_grid
        )
    
    # ---------------------------------------------------------
    # 4. PUZZLE
    # ---------------------------------------------------------
    elif encounter_type == EncounterType.PUZZLE:
        return PuzzleEncounter(
            id=encounter_id,
            name="Ancient Mechanism",
            description="A strange obstacle blocks the path forward.",
            threat_level=threat_level,
            mechanism="Logical / Magical",
            difficulty_class=10 + threat_level,
            reward_hint="A hidden cache of resources.",
            grid=tactical_grid
        )
    
    # ---------------------------------------------------------
    # 5. DISCOVERY (Loot & Lore)
    # ---------------------------------------------------------
    elif encounter_type == EncounterType.DISCOVERY:
        # If the Item_Builder exists, pick a real item ID!
        loot_id = "UNKNOWN_ITEM"
        if ITEM_DB:
            loot_id = random.choice(ITEM_DB).get("id", "UNKNOWN_ITEM")

        return DiscoveryEncounter(
            id=encounter_id,
            name="Hidden Cache",
            description="You stumble upon a remnant of the old world.",
            threat_level=threat_level,
            lore_snippet="A journal detailing the collapse...",
            hidden_item_id=loot_id,
            grid=tactical_grid
        )
    
    # ---------------------------------------------------------
    # 6. DILEMMA
    # ---------------------------------------------------------
    elif encounter_type == EncounterType.DILEMMA:
        return DilemmaEncounter(
            id=encounter_id,
            name="Hard Choice",
            description="A situation requiring a sacrifice.",
            threat_level=threat_level,
            choices=[
                Choice(choice="Intervene and risk injury", cost={"stamina": 2}, reward={"wealth": 10}),
                Choice(choice="Walk away", cost={"composure": -1}, reward={})
            ]
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
