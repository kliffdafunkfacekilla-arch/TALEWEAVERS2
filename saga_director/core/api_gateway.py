import httpx
import logging
import os
import json

class SAGA_API_Gateway:
    def __init__(self):
        self.microservices = {
            "char_engine": os.getenv("CHAR_ENGINE_URL", "http://localhost:8003"),
            "item_foundry": os.getenv("ITEM_FOUNDRY_URL", "http://localhost:8005"),
            "clash_engine": os.getenv("CLASH_ENGINE_URL", "http://localhost:8007"),
            "skill_engine": os.getenv("SKILL_ENGINE_URL", "http://localhost:8006"),
            "encounter_engine": os.getenv("ENCOUNTER_ENGINE_URL", "http://localhost:8004"),
            "world_architect": os.getenv("WORLD_ARCHITECT_URL", "http://localhost:8002"),
            "campaign_weaver": os.getenv("CAMPAIGN_WEAVER_URL", "http://localhost:8010"),
            "dmag_engine": os.getenv("DMAG_ENGINE_URL", "http://localhost:8008"),
            "asset_foundry": os.getenv("ASSET_FOUNDRY_URL", "http://localhost:8012"),
            "chronos": os.getenv("CHRONOS_URL", "http://localhost:9000"),
        }

    async def get_character(self, player_id: str):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.microservices['char_engine']}/api/character/{player_id}")
                return res.json() if res.status_code == 200 else None
        except: return None

    async def resolve_clash(self, attacker_data: dict, defender_data: dict):
        try:
            async with httpx.AsyncClient() as client:
                payload = {"attacker": attacker_data, "defender": defender_data, "environment": {}, "situational_mods": {}}
                res = await client.post(f"{self.microservices['clash_engine']}/api/clash/resolve", json=payload)
                return res.json()
        except: return {"clash_result": "Error", "defender_hp_change": 0}

    async def use_item(self, player_id: str, item_id: str):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{self.microservices['item_foundry']}/api/item/use?player_id={player_id}&item_id={item_id}")
                return res.json()
        except: return {"item_name": "Unknown", "effect": "Nothing happens."}

    async def generate_encounter(self, context: dict):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{self.microservices['encounter_engine']}/api/encounter/generate", json=context)
                return res.json()
        except: return None

    async def register_asset(self, asset_id: str, file_path: str):
        """Registers a generated image with the Asset Foundry."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {"asset_id": asset_id, "source_path": file_path}
                res = await client.post(f"{self.microservices['asset_foundry']}/api/assets/register", json=payload)
                return res.json() if res.status_code == 200 else None
        except: return None

    async def get_hex_details(self, hex_id: int):
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")
        
        node_data = {
            "cell_id": hex_id,
            "biome": "Wilderness",
            "threat_level": 1,
            "faction_owner": "Neutral",
            "tags": [],
            "visual_url": None
        }

        if os.path.exists(MAP_FILE):
            try:
                with open(MAP_FILE, "r") as f:
                    world = json.load(f)
                    for node in world.get("macro_map", []):
                        if node.get("cell_id") == hex_id:
                            node_data.update(node)
            except: pass
            
        return node_data
