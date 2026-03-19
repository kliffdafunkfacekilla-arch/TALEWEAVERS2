import hashlib
import random
import math
import numpy as np
from shapely.geometry import Polygon, Point
from typing import List, Tuple, Dict, Any

class NPCScheduler:
    """Calculates NPC position based on 15-minute intervals using LERP."""
    def __init__(self, npc_id: str, home: Tuple[int, int], work: Tuple[int, int], tavern: Tuple[int, int]):
        self.npc_id = npc_id
        self.locations = {"home": home, "work": work, "tavern": tavern}
        # Schedule: (Start Hour, End Hour, Activity)
        self.schedule = [
            (0.0, 8.0, "home"),
            (8.0, 9.0, "traveling_to_work"),
            (9.0, 17.0, "work"),
            (17.0, 18.0, "traveling_to_tavern"),
            (18.0, 21.0, "tavern"),
            (21.0, 22.0, "traveling_to_home"),
            (22.0, 24.0, "home")
        ]

    def get_position(self, current_hour: float) -> Tuple[Tuple[float, float], str]:
        """Returns (x, y) and status for a 100x100 grid."""
        for start, end, activity in self.schedule:
            if start <= current_hour < end:
                if "traveling" in activity:
                    if activity == "traveling_to_work": p1, p2 = self.locations["home"], self.locations["work"]
                    elif activity == "traveling_to_tavern": p1, p2 = self.locations["work"], self.locations["tavern"]
                    else: p1, p2 = self.locations["tavern"], self.locations["home"]
                    
                    progress = (current_hour - start) / (end - start)
                    curr_x = p1[0] + (p2[0] - p1[0]) * progress
                    curr_y = p1[1] + (p2[1] - p1[1]) * progress
                    return (curr_x, curr_y), "traveling"
                return self.locations[activity], activity
        return self.locations["home"], "sleeping"

class BuildingGenerator:
    """Generates building interiors using Box-and-Slice recursive subdivision."""
    @staticmethod
    def generate_layout(seed: int, width: int = 20, height: int = 20) -> Dict[str, Any]:
        random.seed(seed)
        lot = {"x": 0, "y": 0, "w": width, "h": height}
        # Inset for yard
        yard_inset = 2
        building = {"x": lot["x"]+yard_inset, "y": lot["y"]+yard_inset, 
                    "w": lot["w"]-2*yard_inset, "h": lot["h"]-2*yard_inset}
        
        rooms = []
        # Recursive Subdivision (Depth 1)
        if random.random() > 0.5: # Split Vertical
            split = random.randint(4, building["w"] - 4)
            rooms.append({"type": "ENTRANCE", "x": building["x"], "y": building["y"], "w": split, "h": building["h"]})
            rooms.append({"type": "LIVING", "x": building["x"]+split, "y": building["y"], "w": building["w"]-split, "h": building["h"]})
        else: # Split Horizontal
            split = random.randint(4, building["h"] - 4)
            rooms.append({"type": "ENTRANCE", "x": building["x"], "y": building["y"], "w": building["w"], "h": split})
            rooms.append({"type": "STORAGE", "x": building["x"], "y": building["y"]+split, "w": building["w"], "h": building["h"]-split})
            
        return {"id": seed, "rooms": rooms, "bounds": building}

class WorldPersistence:
    """Handles Delta-State serialization for persistent changes."""
    def __init__(self):
        self.perm_changes: Dict[int, Dict[str, Any]] = {} # hex_id -> {entity_id: delta}

    def save_change(self, hex_id: int, entity_id: str, new_data: Dict[str, Any]):
        if hex_id not in self.perm_changes: self.perm_changes[hex_id] = {}
        if entity_id not in self.perm_changes[hex_id]: self.perm_changes[hex_id][entity_id] = {}
        self.perm_changes[hex_id][entity_id].update(new_data)

    def load_entity(self, hex_id: int, entity_id: str, base_data: Dict[str, Any]) -> Dict[str, Any]:
        delta = self.perm_changes.get(hex_id, {}).get(entity_id, {})
        return {**base_data, **delta}

class WorldManager:
    """Main Orchestrer for the Hierarchical World Engine."""
    def __init__(self, world_seed: int):
        self.world_seed = world_seed
        self.persistence = WorldPersistence()
        self.factions: Dict[str, np.ndarray] = {} # Influence Maps (100x100 world scale)

    def get_local_seed(self, *args) -> int:
        seed_str = "_".join(map(str, [self.world_seed] + list(args)))
        return int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**32)

    def create_hex_mask(self, width: int, height: int, radius: float = 1.0) -> np.ndarray:
        """Bounding Volume Masking: Points-in-Hexagon check."""
        angles = np.linspace(0, 2 * np.pi, 7)
        hex_coords = [(radius * np.cos(a), radius * np.sin(a)) for a in angles]
        hex_poly = Polygon(hex_coords)
        mask = np.zeros((height, width), dtype=bool)
        xs = np.linspace(-radius, radius, width)
        ys = np.linspace(-radius, radius, height)
        for r in range(height):
            for c in range(width):
                if hex_poly.contains(Point(xs[c], ys[r])): mask[r, c] = True
        return mask

    def get_poisson_buildings(self, hex_id: int, min_dist: float = 3.0) -> List[Dict[str, Any]]:
        """Natural clustering for building points in a 20x20 regional grid."""
        rng = random.Random(self.get_local_seed(hex_id, "buildings"))
        points = []
        min_dist_sq = min_dist * min_dist
        for _ in range(50):
            x = rng.randint(0, 19)
            y = rng.randint(0, 19)

            valid = True
            for p in points:
                if (x - p['x'])**2 + (y - p['y'])**2 < min_dist_sq:
                    valid = False
                    break

            if valid:
                points.append({"x": x, "y": y, "type": rng.choice(["HOUSE", "SHOP", "TAVERN"])})
        return points

    def get_local_modifiers(self, hex_id: int) -> Dict[str, float]:
        """Faction Ripple: Global events modify local tactical stats."""
        # This would pull from a real FactionManager in a production scenario
        # Defaulting to standard modifiers
        return {"guard_boost": 1.0, "price_mult": 1.0, "spawn_rate": 1.0}

    @staticmethod
    def upsample_entities(density: float, hex_id: int, entity_type: str) -> int:
        """Calculate actor count from abstract hex density."""
        seed = int(hashlib.md5(f"{hex_id}_{entity_type}".encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        variance = random.uniform(0.8, 1.2)
        return max(1, int(density * 10 * variance))
