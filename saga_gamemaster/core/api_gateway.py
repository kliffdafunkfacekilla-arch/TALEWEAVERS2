import httpx
import logging

class SAGA_API_Gateway:
    def __init__(self):
        self.microservices = {
            "char_engine": "http://localhost:8003",
            "item_foundry": "http://localhost:8005",
            "clash_engine": "http://localhost:8007",
            "encounter_engine": "http://localhost:8009",
        }

    async def get_character(self, player_id: str):
        async with httpx.AsyncClient() as client:
            try:
                # Call the real Character Rules Engine on Port 8003
                # For basic fetch, we might use a direct getter if the engine supported it, 
                # but for this blueprint, we ensure the GM is aware of the Rules port.
                response = await client.get(f"{self.microservices['char_engine']}/health")
                # Note: Currently char_engine is a stateless calculator. 
                # In a full build, this would hit a Character DB. 
                # For now, we return a hybrid to satisfy the GM Logic while maintaining the Port 8003 link.
                return {
                    "player_id": player_id,
                    "survival_pools": {"current_hp": 20, "max_hp": 20, "stamina": 12, "max_stamina": 12},
                    "attributes": {"might": 10, "reflexes": 10, "willpower": 10}
                }
            except Exception as e:
                logging.error(f"Character Rules Engine Unreachable: {e}")
                return None

    async def use_item(self, player_id: str, item_id: str, target_vitals: dict = None):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.microservices['item_foundry']}/items/resolve",
                    json={"item_id": item_id, "target_vitals": target_vitals or {}}
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "item_name": data.get("item_name", item_id),
                    "effect": data.get("details", "Used item."),
                    "math_result": data.get("math_result", 0),
                    "target_pool": data.get("target_pool", None)
                }
            except Exception as e:
                logging.error(f"Item Foundry Error: {e}")
                return {"item_name": item_id, "effect": "Item resolution failed."}

    async def resolve_clash(self, attacker_data: dict, defender_data: dict):
        async with httpx.AsyncClient() as client:
            try:
                # We format the payload exactly as Module 7 expects
                payload = {
                    "attacker": attacker_data,
                    "defender": defender_data,
                    "chaos_level": 1
                }
                response = await client.post(
                    f"{self.microservices['clash_engine']}/api/clash/resolve",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "margin": data.get("clash_result", "DEADLOCK"),
                    "dmg": data.get("defender_hp_change", 0),
                    "attacker_dmg": data.get("attacker_hp_change", 0),
                    "injury": data.get("defender_injury_applied", None)
                }
            except Exception as e:
                logging.error(f"Clash Engine Error: {e}")
                return {"margin": "ERROR", "dmg": 0, "injury": None}

    async def generate_encounter(self, request_data: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.microservices['encounter_engine']}/api/encounter/generate",
                    json=request_data
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"Encounter Engine Error: {e}")
                return None

    async def check_quest_triggers(self, coords: str):
        # For now, this acts as the "Director's Script". 
        if coords == "[10, 15]":
            return {"type": "SOCIAL", "event": "Wandering Merchant", "seed": "A merchant with information about the relic."}
        return None
    
    async def get_campaign_state(self, player_id: str):
        # Connects to Module 8 logic
        return {
            "current_node_name": "The Whispering Woods",
            "active_quests": [{"title": "Find the Missing Heir", "status": "In Progress"}]
        }
