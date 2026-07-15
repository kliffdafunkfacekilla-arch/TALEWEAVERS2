import numpy as np

class WorldBuffers:
    """
    Structure of Arrays (SoA) layout for high-performance World Simulation in Python.
    Inspired by the Omnis Engine architecture for 1M+ cell grids.
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.size = width * height
        
        # --- Core Layers ---
        self.elevation = np.zeros(self.size, dtype=np.float32)
        self.temperature = np.zeros(self.size, dtype=np.float32)
        self.moisture = np.zeros(self.size, dtype=np.float32)
        
        # --- Simulation Layers ---
        self.wind_dx = np.zeros(self.size, dtype=np.float32)
        self.wind_dy = np.zeros(self.size, dtype=np.float32)
        
        self.flux = np.zeros(self.size, dtype=np.float32)
        self.chaos = np.zeros(self.size, dtype=np.float32)
        
        self.infrastructure = np.zeros(self.size, dtype=np.uint8)
        self.wealth = np.zeros(self.size, dtype=np.float32)
        self.defense = np.zeros(self.size, dtype=np.float32)
        
        # 0: Wild, 1: Outpost, 2: Village, 3: Town, 4: City
        self.civ_tier = np.zeros(self.size, dtype=np.uint8)
        self.building_id = np.zeros(self.size, dtype=np.int32)
        
        # Flattened 2D array [cell * 8] for 8 resource types
        self.resource_inventory = np.zeros(self.size * 8, dtype=np.uint16)

    def get_index(self, x: int, y: int) -> int:
        return y * self.width + x

class EntityManager:
    """
    Basic Entity Component System (ECS) for managing Actors, NPCs, and dynamic objects.
    """
    def __init__(self):
        self.next_id = 1
        self.entities = set()
        
        # Components
        self.positions = {}       # entity_id -> (x, y)
        self.stats = {}           # entity_id -> dict
        self.intents = {}         # entity_id -> str (pending LLM action)

    def create_entity(self) -> int:
        eid = self.next_id
        self.next_id += 1
        self.entities.add(eid)
        return eid

    def add_position(self, entity_id: int, x: int, y: int):
        self.positions[entity_id] = (x, y)

    def update(self):
        # Tick logic goes here
        pass
