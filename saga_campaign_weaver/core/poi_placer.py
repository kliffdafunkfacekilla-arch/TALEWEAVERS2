import random

class POIPlacer:
    def __init__(self, grid_size=96):
        self.grid_size = grid_size

    def place_node_on_grid(self, quest_node: dict, grid_data: list) -> dict:
        """
        Takes a Weaver QuestNode and the 96x96 IDW grid data,
        returning the exact (X, Y) coordinates for the POI.
        
        grid_data format: list of dicts with {x, y, elevation, moisture, is_water}
        """
        valid_tiles = []
        encounter_type = quest_node.get("encounter_type", "EXPLORATION").upper()
        
        # 1. Filter out illegal tiles (e.g., deep water) for land-based POIs
        land_tiles = [t for t in grid_data if not t.get("is_water", False)]

        # 2. Score tiles based on the Weaver's Encounter Type
        if encounter_type == "COMBAT" and "tower" in quest_node.get("description", "").lower():
            # Watchtowers or forts want HIGH elevation
            land_tiles.sort(key=lambda t: t.get("elevation", 0), reverse=True)
            valid_tiles = land_tiles[:50] # Take the top 50 highest peaks
            
        elif encounter_type == "SOCIAL" or "camp" in quest_node.get("description", "").lower():
            # Camps want flat ground (average elevation) near water (high moisture)
            flat_tiles = [t for t in land_tiles if 0.3 < t.get("elevation", 0) < 0.6]
            flat_tiles.sort(key=lambda t: t.get("moisture", 0), reverse=True)
            valid_tiles = flat_tiles[:50] # Take the top 50 flattest, most lush spots
            
        elif encounter_type == "HAZARD":
            # Hazards like monster dens spawn in low, dry, or extreme terrain
            land_tiles.sort(key=lambda t: t.get("elevation", 0))
            valid_tiles = land_tiles[:50] # Take the 50 lowest valleys/caves
            
        else:
            # Default: Pick any valid land tile
            valid_tiles = land_tiles

        # 3. Select a specific coordinate from the valid list
        if not valid_tiles:
            # Fallback if the map is entirely water or anomalous 
            chosen_tile = random.choice(grid_data)
        else:
            chosen_tile = random.choice(valid_tiles)

        # 4. Return the injected payload for the frontend
        return {
            "node_id": quest_node.get("id", "poi_01"),
            "title": quest_node.get("title", "Unknown Location"),
            "encounter_type": encounter_type,
            "coordinates": {
                "x": chosen_tile["x"],
                "y": chosen_tile["y"]
            },
            "terrain_context": {
                "elevation": chosen_tile.get("elevation"),
                "moisture": chosen_tile.get("moisture")
            }
        }
