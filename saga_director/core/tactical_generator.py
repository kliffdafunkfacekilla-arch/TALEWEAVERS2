import random
import hashlib
from typing import List, Dict, Any
from .world_manager import WorldManager, BuildingGenerator, NPCScheduler

class TacticalGenerator:
    """Generates a 4-layer hierarchical environment with deterministic, persistent logic."""
    
    _world_manager = None

    @classmethod
    def set_world_manager(cls, wm: WorldManager):
        cls._world_manager = wm

    @classmethod
    def get_wm(cls) -> WorldManager:
        if cls._world_manager is None:
            # Default world seed if not set
            cls._world_manager = WorldManager(world_seed=918273)
        return cls._world_manager

    @classmethod
    def generate_region_map(cls, biome: str, hex_id: int) -> Dict[str, Any]:
        """Layer 2: 20x20 Regional Grid with Poisson-Disc building placement."""
        width, height = 20, 20
        wm = cls.get_wm()
        mask = wm.create_hex_mask(width, height)
        
        grid = [["NULL" for _ in range(width)] for _ in range(height)]
        
        # Base Wilderness
        for r in range(height):
            for c in range(width):
                if mask[r, c]: grid[r][c] = "WILDERNESS"
                    
        # Poisson Buildings (Strategic points)
        buildings = wm.get_poisson_buildings(hex_id)
        for b in buildings:
            if 0 <= b['x'] < width and 0 <= b['y'] < height:
                if mask[b['y'], b['x']]: 
                    grid[b['y']][b['x']] = b['type']
                            
        return {
            "type": "REGIONAL", "hex_id": hex_id,
            "width": width, "height": height,
            "grid": grid, "biome": biome,
            "points_of_interest": buildings
        }

    @classmethod
    def generate_local_grid(cls, biome: str, hex_id: int, rx: int, ry: int) -> Dict[str, Any]:
        """Layer 3: 100x100 Local Grid with deterministic nature."""
        width, height = 100, 100
        wm = cls.get_wm()
        
        sub_seed = wm.get_local_seed(hex_id, rx, ry)
        rng = random.Random(sub_seed)
        grid = [["CLEAR" for _ in range(width)] for _ in range(height)]
        
        # Ambient Nature
        for r in range(height):
            for c in range(width):
                if rng.random() < 0.02: grid[r][c] = "THICKET"
                elif rng.random() < 0.005: grid[r][c] = "ROCK_PILE"
                    
        return {
            "type": "LOCAL", "coords": (rx, ry),
            "width": width, "height": height,
            "grid": grid, "biome": biome
        }

    @classmethod
    def generate_ambient_encounter(cls, biome: str, hex_id: int, lx: int, ly: int, current_hour: float = 12.0, densities: Dict[str, float] = {}, external_npcs: List[Dict] = [], player_sprite: Dict = None) -> Dict[str, Any]:
        """Layer 4: 100x100 Tactical Grid with materialized buildings and scheduled NPCs."""
        width, height = 100, 100
        wm = cls.get_wm()
        
        grid_data = [["EMPTY" for _ in range(width)] for _ in range(height)]
        
        # 1. Building Interior Generation (Box-and-Slice)
        b_seed = wm.get_local_seed(hex_id, "building", lx, ly)
        layout = BuildingGenerator.generate_layout(b_seed)
        
        # Check Persistence: Is the building ruined?
        b_data = wm.persistence.load_entity(hex_id, f"building_{lx}_{ly}", {"is_ruined": False})
        
        for room in layout["rooms"]:
            for r in range(room["y"], room["y"] + room["h"]):
                for c in range(room["x"], room["x"] + room["w"]):
                    if b_data["is_ruined"]:
                        if random.random() < 0.3: grid_data[r][c] = "DEBRIS"
                        else: grid_data[r][c] = "EMPTY"
                    else:
                        grid_data[r][c] = "FLOOR"
                        # Walls with gaps for doors
                        if (r == room["y"] or r == room["y"]+room["h"]-1 or c == room["x"] or c == room["x"]+room["w"]-1):
                            grid_data[r][c] = "WALL"
        
        # 2. Tokens: Player
        player_x, player_y = width // 2, height // 2
        tokens = [{
            "id": "PLAYER_1", "name": "You", "x": player_x, "y": player_y, 
            "isPlayer": True, "color": 0x3B82F6,
            "composite_sprite": player_sprite
        }]
        
        # 3. Tokens: Scheduled NPCs (Local Residents)
        npc_seed = wm.get_local_seed(hex_id, "npcs", lx, ly)
        rng = random.Random(npc_seed)
        
        resident_ids = [f"RESIDENT_{hex_id}_{lx}_{ly}_{i}" for i in range(2)]
        for npc_id in resident_ids:
            h_x, h_y = rng.randint(layout["bounds"]["x"], layout["bounds"]["x"]+layout["bounds"]["w"]), rng.randint(layout["bounds"]["y"], layout["bounds"]["y"]+layout["bounds"]["h"])
            w_x, w_y = rng.randint(0, 99), rng.randint(0, 99)
            t_x, t_y = rng.randint(0, 99), rng.randint(0, 99)
            
            scheduler = NPCScheduler(npc_id, (h_x, h_y), (w_x, w_y), (t_x, t_y))
            pos, status = scheduler.get_position(current_hour)
            
            p_data = wm.persistence.load_entity(hex_id, npc_id, {"is_dead": False, "hp": 10})
            if not p_data["is_dead"]:
                tokens.append({
                    "id": npc_id, "name": "Villager", "status": status,
                    "x": int(pos[0]), "y": int(pos[1]), "isPlayer": False,
                    "hp": p_data["hp"], "color": 0xF59E0B
                })

        # 4. Tokens: External NPCs (from Context/Events)
        for ext_npc in external_npcs:
            ex, ey = ext_npc.get("rx", rng.randint(0, 99)), ext_npc.get("ry", rng.randint(0, 99))
            tokens.append({
                "id": ext_npc.get("event_id", f"EXT_{random.randint(0,999)}"),
                "name": ext_npc.get("name", "Unknown"),
                "status": ext_npc.get("type", "Encounter"),
                "x": int(ex), "y": int(ey), "isPlayer": False,
                "hp": 20, "color": 0xEF4444 if ext_npc.get("attitude") == "HOSTILE" else 0x10B981
            })

        return {
            "encounter_id": f"tactical_{hex_id}_{lx}_{ly}",
            "gridWidth": width,
            "gridHeight": height,
            "grid": grid_data,
            "tokens": tokens,
            "data": {
                "category": "EXPLORATION",
                "title": biome.title() + " Tactical Layer",
                "narrative_prompt": f"You are exploring a {biome.lower()} near local coordinates {lx}, {ly}.",
                "npcs": [],
                "enemies": []
            },
            "metadata": {
                "biome": biome,
                "current_time": f"{int(current_hour)}:00",
                "building_layout": layout
            }
        }
