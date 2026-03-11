import httpx
import logging
import os
import json

# Import local consolidated functions
from core.weaver import (
    generate_campaign_framework,
    generate_regional_arc,
    generate_local_sidequest,
    generate_tactical_errand
)
from core.generator import generate_encounter
from core.encounter_schemas import EncounterRequest

class SAGA_API_Gateway:
    def __init__(self):
        self.microservices = {
            "rules_engine": os.getenv("RULES_ENGINE_URL", "http://localhost:8014"),
            "world_architect": os.getenv("WORLD_ARCHITECT_URL", "http://localhost:8013"),
            "asset_foundry": os.getenv("ASSET_FOUNDRY_URL", "http://localhost:8012"),
            "chronos": os.getenv("CHRONOS_URL", "http://localhost:9002"),
        }

    async def get_character(self, player_id: str):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.microservices['rules_engine']}/api/rules/character/{player_id}")
                return res.json() if res.status_code == 200 else None
        except: return None

    async def resolve_clash(self, attacker_data: dict, defender_data: dict):
        try:
            async with httpx.AsyncClient() as client:
                payload = {"attacker": attacker_data, "defender": defender_data, "environment": {}, "situational_mods": {}}
                res = await client.post(f"{self.microservices['rules_engine']}/api/rules/clash/resolve", json=payload)
                return res.json()
        except: return {"clash_result": "Error", "defender_hp_change": 0}

    async def use_item(self, player_id: str, item_id: str):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{self.microservices['rules_engine']}/api/rules/items/resolve", json={"item_id": item_id})
                return res.json()
        except: return {"item_name": "Unknown", "effect": "Nothing happens."}

    async def generate_encounter(self, context: dict):
        try:
            # Use direct internal call instead of HTTP
            req = EncounterRequest(**context)
            result = generate_encounter(req)
            return result.model_dump()
        except Exception as e:
            logging.error(f"[GATEWAY] Encounter generation failed: {e}")
            return None

    async def generate_regional_arc(self, saga_beat: dict, region_context: dict, context_packet: dict = None):
        """Tier 2: Generates a 2-3 step sub-plot bridging two Saga Beats."""
        try:
            # Use direct internal call instead of HTTP
            result = await generate_regional_arc(saga_beat, region_context, context_packet)
            return [r.model_dump() for r in result]
        except Exception as e:
            logging.error(f"[GATEWAY] Regional arc generation failed: {e}")
            return []

    async def generate_local_sidequest(self, hex_context: dict, context_packet: dict = None):
        """Tier 3: Generates a hex-specific side quest."""
        try:
            # Use direct internal call instead of HTTP
            result = await generate_local_sidequest(hex_context, context_packet)
            return result.model_dump() if result else None
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
            # Use direct internal call instead of HTTP
            framework = await generate_campaign_framework(
                characters=request_payload.get("characters", []),
                world_state=request_payload.get("world_state", {}),
                settings=request_payload.get("settings", {}),
                history=request_payload.get("history", []),
                context_packet=request_payload.get("context_packet")
            )
            return framework.model_dump() if framework else None
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
