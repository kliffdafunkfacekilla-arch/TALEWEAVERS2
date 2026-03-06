import random
from typing import List, Dict, Any

class TacticalGenerator:
    """Generates 5ft-scale tactical environments (Encounter data) for Tier 5."""
    
    @staticmethod
    def generate_ambient_encounter(biome: str, hex_id: int, npcs: List[Dict] = []) -> Dict[str, Any]:
        """Creates a grid-based ambient area (15x15) for the player to land in."""
        width = 15
        height = 15
        
        # 1. Generate Grid (0 for empty, 1 for obstacle)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        
        # 2. Add Biome-specific Props
        prop_types = ["TREE", "ROCK", "WALL", "BARREL", "CRATE"]
        prop_density = 0.1 # 10% obstacles
        
        if biome.upper() == "FOREST":
            props = ["TREE", "ROCK"]
            prop_density = 0.15
        elif biome.upper() == "DUNGEON" or biome.upper() == "RUINS":
            props = ["WALL", "BARREL", "TABLE", "CHEST"]
            prop_density = 0.2
        else:
            props = ["ROCK", "CRATE"]
            prop_density = 0.05

        grid_data = [["EMPTY" for _ in range(width)] for _ in range(height)]
        
        for r in range(height):
            for c in range(width):
                if random.random() < prop_density:
                    grid_data[r][c] = random.choice(props)
        
        # 3. Position Player (Center)
        player_x, player_y = width // 2, height // 2
        grid_data[player_y][player_x] = "EMPTY" # Ensure player is not in a tree
        
        tokens = [
            {
                "id": "PLAYER_001",
                "name": "You",
                "x": player_x,
                "y": player_y,
                "isPlayer": True,
                "color": 0x3B82F6
            }
        ]
        
        # 4. Position NPCs
        for i, npc in enumerate(npcs):
            # Find an empty spot
            nx, ny = random.randint(1, width-2), random.randint(1, height-2)
            while grid_data[ny][nx] != "EMPTY" or (nx == player_x and ny == player_y):
                nx, ny = random.randint(1, width-2), random.randint(1, height-2)
            
            tokens.append({
                "id": f"npc_{i}",
                "name": npc["name"],
                "type": npc["type"],
                "faction": npc.get("faction"),
                "x": nx,
                "y": ny,
                "isPlayer": False,
                "color": 0xF59E0B,
                "current_hp": 10,
                "max_hp": 10
            })

        return {
            "encounter_id": f"ambient_{hex_id}",
            "gridWidth": width,
            "gridHeight": height,
            "grid": grid_data,
            "tokens": tokens,
            "data": {
                "category": "AMBIENT",
                "title": f"Local {biome.title()} Area",
                "narrative_prompt": f"You are in a 5ft-scale area of {biome}. Explore, find loot, or talk to and greet those nearby.",
                "biome": biome
            },
            "interactionHistory": []
        }
