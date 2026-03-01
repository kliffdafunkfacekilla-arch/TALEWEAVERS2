import httpx
import logging

class SAGA_API_Gateway:
    def __init__(self):
        self.microservices = {
            "char_engine": "http://localhost:8003",
            "item_foundry": "http://localhost:8005",
            "clash_engine": "http://localhost:8007",
            "encounter_engine": "http://localhost:8009",
            "campaign_weaver": "http://localhost:8010",
        }

    async def get_character(self, player_id: str):
        async with httpx.AsyncClient() as client:
            try:
                mock_payload = {
                    "name": player_id,
                    "base_attributes": {"might": 3, "endurance": 3, "vitality": 3, "fortitude": 3, "reflexes": 3, "finesse": 3, "knowledge": 3, "logic": 3, "charm": 3, "willpower": 3, "awareness": 3, "intuition": 3},
                    "evolutions": {"species_base": "HUMAN"},
                    "selected_powers": [],
                    "equipped_loadout": {},
                    "tactical_skills": {}
                }
                response = await client.post(f"{self.microservices['char_engine']}/api/rules/character/calculate", json=mock_payload)
                if response.status_code == 200:
                    data = response.json()
                    v = data.get("vitals", {})
                    return {
                        "player_id": player_id,
                        "survival_pools": {
                            "current_hp": v.get("max_hp", 20), "max_hp": v.get("max_hp", 20),
                            "stamina": v.get("max_stamina", 12), "max_stamina": v.get("max_stamina", 12),
                            "focus": v.get("max_focus", 10), "max_focus": v.get("max_focus", 10),
                            "composure": v.get("max_composure", 10), "max_composure": v.get("max_composure", 10)
                        },
                        "attributes": data.get("attributes", {})
                    }
                return {
                    "player_id": player_id,
                    "survival_pools": {"current_hp": 20, "max_hp": 20, "stamina": 12, "max_stamina": 12, "focus": 10, "max_focus": 10, "composure": 10, "max_composure": 10},
                    "attributes": {"might": 3, "reflexes": 3, "willpower": 3}
                }
            except Exception as e:
                logging.error(f"Character Rules Engine Error: {e}")
                return {
                    "player_id": player_id,
                    "survival_pools": {"current_hp": 20, "max_hp": 20, "stamina": 12, "max_stamina": 12, "focus": 10, "max_focus": 10, "composure": 10, "max_composure": 10},
                    "attributes": {"might": 3, "reflexes": 3, "willpower": 3}
                }

    async def generate_framework(self, characters: list, world_state: dict, settings: dict, history: list = None):
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "characters": characters,
                    "world_state": world_state,
                    "settings": settings,
                    "history": history or []
                }
                response = await client.post(
                    f"{self.microservices['campaign_weaver']}/api/weaver/framework",
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"Campaign Weaver Framework Error: {e}")
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

    async def resolve_clash(self, attacker_data: dict, defender_data: dict, chaos_level: int = 1, 
                            attacker_adv: bool = False, attacker_dis: bool = False,
                            defender_adv: bool = False, defender_dis: bool = False):
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "attacker": attacker_data,
                    "defender": defender_data,
                    "chaos_level": chaos_level,
                    "attacker_advantage": attacker_adv,
                    "attacker_disadvantage": attacker_dis,
                    "defender_advantage": defender_adv,
                    "defender_disadvantage": defender_dis
                }
                response = await client.post(
                    f"{self.microservices['clash_engine']}/api/clash/resolve",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "clash_result": data.get("clash_result", "DEADLOCK"),
                    "margin": data.get("margin", 0),
                    "defender_hp_change": data.get("defender_hp_change", 0),
                    "attacker_hp_change": data.get("attacker_hp_change", 0),
                    "defender_composure_change": data.get("defender_composure_change", 0),
                    "attacker_composure_change": data.get("attacker_composure_change", 0),
                    "defender_injury_applied": data.get("defender_injury_applied", None),
                    "chaos_effect_triggered": data.get("chaos_effect_triggered", None)
                }
            except Exception as e:
                logging.error(f"Clash Engine Error: {e}")
                return {"clash_result": "ERROR", "margin": 0}

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

    async def generate_regional_arc(self, saga_beat: dict, region_context: dict):
        async with httpx.AsyncClient() as client:
            try:
                payload = {"saga_beat": saga_beat, "region_context": region_context}
                response = await client.post(
                    f"{self.microservices['campaign_weaver']}/api/weaver/arc",
                    json=payload,
                    timeout=20.0
                )
                return response.json()
            except Exception as e:
                logging.error(f"Gateway Error (generate_regional_arc): {e}")
                return []

    async def generate_local_sidequest(self, hex_context: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.microservices['campaign_weaver']}/api/weaver/sidequest",
                    json={"hex_context": hex_context},
                    timeout=20.0
                )
                return response.json()
            except Exception as e:
                logging.error(f"Gateway Error (generate_local_sidequest): {e}")
                return None

    async def generate_tactical_errand(self, location: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.microservices['campaign_weaver']}/api/weaver/errand",
                    json={"location": location},
                    timeout=10.0
                )
                return response.json()
            except Exception as e:
                logging.error(f"Gateway Error (generate_tactical_errand): {e}")
                return None
