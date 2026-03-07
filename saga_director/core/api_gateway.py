import httpx
import logging
import os
import json

class SAGA_API_Gateway:
    def __init__(self):
        self.microservices = {
            "char_engine": os.getenv("CHAR_ENGINE_URL", "http://localhost:8014"),
            "item_foundry": os.getenv("ITEM_FOUNDRY_URL", "http://localhost:8016"),
            "clash_engine": os.getenv("CLASH_ENGINE_URL", "http://localhost:8018"),
            "skill_engine": os.getenv("SKILL_ENGINE_URL", "http://localhost:8017"),
            "encounter_engine": os.getenv("ENCOUNTER_ENGINE_URL", "http://localhost:8015"),
            "world_architect": os.getenv("WORLD_ARCHITECT_URL", "http://localhost:8013"),
            "campaign_weaver": os.getenv("CAMPAIGN_WEAVER_URL", "http://localhost:8020"),
            "dmag_engine": os.getenv("DMAG_ENGINE_URL", "http://localhost:8019"),
            "asset_foundry": os.getenv("ASSET_FOUNDRY_URL", "http://localhost:8021"),
            "chronos": os.getenv("CHRONOS_URL", "http://localhost:9002"),
            "lore": os.getenv("LORE_VAULT_URL", "http://localhost:8011"),
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

    async def generate_regional_arc(self, saga_beat: dict, region_context: dict, context_packet: dict = None):
        """Tier 2: Generates a 2-3 step sub-plot bridging two Saga Beats."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "saga_beat": saga_beat,
                    "region_context": region_context,
                    "context_packet": context_packet
                }
                res = await client.post(f"{self.microservices['campaign_weaver']}/api/weaver/arc", json=payload)
                return res.json() if res.status_code == 200 else []
        except Exception as e:
            logging.error(f"[GATEWAY] Regional arc generation failed: {e}")
            return []

    async def generate_local_sidequest(self, hex_context: dict, context_packet: dict = None):
        """Tier 3: Generates a hex-specific side quest."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "hex_context": hex_context,
                    "context_packet": context_packet
                }
                res = await client.post(f"{self.microservices['campaign_weaver']}/api/weaver/sidequest", json=payload)
                return res.json() if res.status_code == 200 else None
        except Exception as e:
            logging.error(f"[GATEWAY] Local sidequest generation failed: {e}")
            return None

    async def register_asset(self, asset_id: str, file_path: str):
        """Registers a generated image with the Asset Foundry."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {"asset_id": asset_id, "source_path": file_path}
                res = await client.post(f"{self.microservices['asset_foundry']}/api/assets/register", json=payload)
                return res.json() if res.status_code == 200 else None
        except: return None

    async def generate_campaign_framework(self, request_payload: dict):
        """Builds the 8-stage mastery plot upon campaign setup."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.microservices['campaign_weaver']}/api/weaver/framework", json=request_payload)
                return res.json() if res.status_code == 200 else None
        except Exception as e:
            logging.error(f"[GATEWAY] Campaign framework generation failed: {e}")
            return None

    async def get_hex_details(self, hex_id: int):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.microservices['world_architect']}/api/world/hex/{hex_id}")
                if res.status_code == 200:
                    data = res.json()
                    return data.get("hex", {})
        except Exception as e:
            logging.error(f"[GATEWAY] Hex ID lookup failed: {e}")
            
        # Fallback to empty node data if API fails
        return {
            "cell_id": hex_id,
            "biome": "Wilderness",
            "threat_level": 1,
            "faction_owner": "Neutral",
            "tags": [],
            "visual_url": None
        }
