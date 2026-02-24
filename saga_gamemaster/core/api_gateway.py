import httpx
import logging

class SAGA_API_Gateway:
    def __init__(self):
        self.microservices = {
            "char_engine": "http://localhost:8003",
            "item_foundry": "http://localhost:8005",
            "clash_engine": "http://localhost:8007",
        }

    async def get_character(self, player_id: str):
        # In a full build, this fetches from Module 3's DB. 
        # For now, we return a valid dict so the GM App doesn't crash.
        return {
            "player_id": player_id,
            "survival_pools": {"current_hp": 15, "max_hp": 20, "stamina": 8, "max_stamina": 10}
        }

    async def use_item(self, player_id: str, item_id: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.microservices['item_foundry']}/items/resolve",
                    json={"item_id": item_id, "target_vitals": {}}
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "item_name": data.get("item_name", item_id),
                    "effect": data.get("details", "Used item.")
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
                    "injury": data.get("defender_injury_applied", None)
                }
            except Exception as e:
                logging.error(f"Clash Engine Error: {e}")
                return {"margin": "ERROR", "dmg": 0, "injury": None}

    async def check_quest_triggers(self, coords: str):
        # For now, this acts as the "Director's Script". 
        if coords == "[10, 15]":
            return {"type": "AMBUSH", "event": "Bandit Ambush"}
        return None
    
    async def get_campaign_state(self, player_id: str):
        # Connects to Module 8 logic
        return {
            "current_node_name": "The Whispering Woods",
            "active_quests": [{"title": "Find the Missing Heir", "status": "In Progress"}]
        }
