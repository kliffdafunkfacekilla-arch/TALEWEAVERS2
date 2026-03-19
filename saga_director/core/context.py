import json
import os
import httpx
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import CampaignState, WorldEventsLog
from .database import SessionLocal
from .day_clock import DayClock
from .reputation import FactionReputation
from .api_gateway import SAGA_API_Gateway

logger = logging.getLogger("saga_director.context")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent.parent
DATA_DIR    = BASE_DIR / "data"
WORLD_EVENTS_FILE = DATA_DIR / "world_events.json"

class ContextAssembler:
    def __init__(self):
        self.gateway = SAGA_API_Gateway()
        self.npc_persistence_file = DATA_DIR / "named_npcs.json"
        self.place_persistence_file = DATA_DIR / "named_places.json"

    async def assemble(self, campaign_id: str, hex_id: int, day_phase: str, current_tick: int) -> Dict[str, Any]:
        """
        Gathers all available data for a specific hex and time.
        1. Lore query from ChromaDB
        2. Active NPCs nearby (calculated from world_events.json)
        3. Faction attitudes (reputation.py)
        4. Region state (Chronos save)
        5. Persistent NPCs and places
        """
        logger.info(f"[CONTEXT] Assembling context for Campaign {campaign_id}, Hex {hex_id}, Phase {day_phase}")
        
        # ── 1. Get Hex Details & Lore ─────────────────────────────────────
        hex_data = await self.gateway.get_hex_details(hex_id)
        biome = hex_data.get("biome", "Wilderness")
        
        # Semantic search for lore context
        lore_context = await self._query_lore(f"Lore and myths about {biome} biomes and nearby landmarks in hex {hex_id}")
        
        # ── 2. Reputation & Attitudes ────────────────────────────────────
        rep = FactionReputation(campaign_id)
        attitudes = rep.get_all_attitudes()
        
        # ── 3. Active NPCs & World Events ─────────────────────────────────
        world_events = await self._load_world_events()
        active_npcs = self._calculate_active_npcs(world_events, hex_id, day_phase, current_tick, attitudes)
        
        # ── 4. Rumours ───────────────────────────────────────────────────
        rumours = self._calculate_rumours(world_events, active_npcs, hex_id)
        
        # ── 5. Passive Region State ──────────────────────────────────────
        # This would ideally come from Chronos save, but we can infer from hex_data for now
        region_state = {
            "dominant_faction": hex_data.get("faction_owner", "Neutral"),
            "threat_level": hex_data.get("threat_level", 1),
            "chaos_adjacent": hex_data.get("chaos_adjacent", False),
        }

        # ── 6. Persistent Named Entities ────────────────────────────────
        persistent_npcs = await self._load_persistent_npcs(campaign_id, hex_id)
        persistent_places = await self._load_persistent_places(campaign_id, hex_id)

        # ── 7. Build Packet ─────────────────────────────────────────────
        packet = {
            "location": {
                "hex_id": hex_id,
                "biome": biome,
                "named_place": persistent_places[0]["name"] if persistent_places else None,
                "persistent_places": persistent_places
            },
            "day_phase": day_phase,
            "lore_context": lore_context,
            "active_npcs": active_npcs + persistent_npcs,
            "faction_attitudes": attitudes,
            "region_state": region_state,
            "rumours": rumours,
            "current_tick": current_tick
        }
        
        return packet

    async def _query_lore(self, query: str) -> List[str]:
        """Calls the saga_lore_module to get relevant context."""
        url = f"{self.gateway.microservices['lore']}/api/lore/search"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json={"query": query, "top_k": 3})
                if res.status_code == 200:
                    results = res.json().get("results", [])
                    return [f"[{r['category']}] {r['title']}: {r['content'][:200]}..." for r in results]
        except Exception as e:
            logger.error(f"[CONTEXT] Lore query failed: {e}")
        return []

    async def _load_world_events(self) -> Dict[str, Any]:
        if not WORLD_EVENTS_FILE.exists():
            return {"events": []}
        def _read():
            try:
                with open(WORLD_EVENTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"events": []}
        return await asyncio.to_thread(_read)

    def _calculate_active_npcs(self, world_events: Dict[str, Any], hex_id: int, day_phase: str, current_tick: int, attitudes: dict) -> List[Dict]:
        """Filter and position NPCs based on time and location."""
        active = []
        events = world_events.get("events", [])
        
        for ev in events:
            # Check if event is active in this phase
            if day_phase not in ev.get("day_phase_active", []):
                continue
            
            # Simple radial filter for now (within 3 hexes)
            ev_hex = ev.get("hex")
            if ev_hex:
                # Static events like Bandit Camps
                try:
                    ev_hex_id = int(ev_hex.replace("hex_", ""))
                    # Since hex IDs are generated left-to-right, top-to-bottom on a 200x200 grid
                    grid_width = 200
                    ev_y, ev_x = divmod(ev_hex_id, grid_width)
                    my_y, my_x = divmod(hex_id, grid_width)
                    
                    dist = max(abs(ev_x - my_x), abs(ev_y - my_y))
                    
                    if dist <= 3:
                        active.append({
                            "event_id": ev.get("id"),
                            "name": ev.get("npc_name"),
                            "type": ev.get("npc_type"),
                            "faction": ev.get("faction"),
                            "attitude": attitudes.get(ev.get("faction"), "NEUTRAL"),
                            "description": f"Located at {ev_hex}",
                            "rx": ev.get("rx", 10),
                            "ry": ev.get("ry", 10)
                        })
                except: pass
            
            elif ev.get("type") == "TRADE_CARAVAN":
                # Moving events: calculate current position interpolate
                start_tick = ev["departs_tick"]
                end_tick = ev["arrives_tick"]
                total = ev["total_days"]
                elapsed = current_tick - start_tick
                
                if 0 <= elapsed <= total:
                    # In a real system we'd find the hex along the road
                    # For now we'll just say it's "on the road nearby" if certain conditions met
                    # Simplified placeholder:
                    active.append({
                        "event_id": ev.get("id"),
                        "name": ev.get("npc_name"),
                        "type": ev.get("npc_type"),
                        "faction": ev.get("faction"),
                        "attitude": attitudes.get(ev.get("faction"), "NEUTRAL"),
                        "description": f"Travelling from {ev.get('origin_faction')} towards {ev.get('destination_faction')}"
                    })

        return active

    def _calculate_rumours(self, world_events: Dict[str, Any], active_npcs: List[Dict], current_hex: int) -> List[str]:
        """ Surface rumours derived from carriers currently in the player's vicinity. """
        rumours = []
        active_ev_ids = [n.get("event_id") for n in active_npcs if n.get("event_id")]
        
        events = world_events.get("events", [])
        for ev in events:
            # If carrier is nearby or event is major (Major events are known by all)
            # Or if the event is a war/surge that everyone knows
            has_nearby_carrier = any(c in active_ev_ids for c in ev.get("carrier_npcs", []))
            
            if ev.get("rumour_text") and (ev.get("major_event") or has_nearby_carrier):
                rumours.append(ev["rumour_text"])
        
        return list(set(rumours))[:3]

    async def _load_persistent_npcs(self, campaign_id: str, hex_id: int) -> List[Dict]:
        if not self.npc_persistence_file.exists(): return []
        def _read():
            try:
                with open(self.npc_persistence_file, "r") as f:
                    data = json.load(f).get(campaign_id, {})
                    # Filter NPCs near this hex
                    return [v for k, v in data.items() if v.get("last_seen_hex") == f"hex_{hex_id}"]
            except: return []
        return await asyncio.to_thread(_read)

    async def _load_persistent_places(self, campaign_id: str, hex_id: int) -> List[Dict]:
        if not self.place_persistence_file.exists(): return []
        def _read():
            try:
                with open(self.place_persistence_file, "r") as f:
                    data = json.load(f).get(campaign_id, {})
                    return [v for k, v in data.items() if v.get("hex") == f"hex_{hex_id}"]
            except: return []
        return await asyncio.to_thread(_read)

    def record_place(self, campaign_id: str, place_name: str, hex_id: int, place_type: str, notes: str, current_tick: int = 0):
        """Saves a new named place to persistence."""
        data = {}
        if self.place_persistence_file.exists():
            with open(self.place_persistence_file, "r") as f:
                data = json.load(f)
        
        campaign_data = data.setdefault(campaign_id, {})
        campaign_data[place_name] = {
            "name": place_name,
            "hex": f"hex_{hex_id}",
            "type": place_type,
            "notes": notes,
            "created_tick": current_tick 
        }
        
        with open(self.place_persistence_file, "w") as f:
            json.dump(data, f, indent=2)

    def record_npc(self, campaign_id: str, npc_name: str, hex_id: int, faction: str, attitude: str):
        """Saves or updates a named NPC."""
        data = {}
        if self.npc_persistence_file.exists():
            with open(self.npc_persistence_file, "r") as f:
                data = json.load(f)
        
        campaign_data = data.setdefault(campaign_id, {})
        campaign_data[npc_name] = {
            "name": npc_name,
            "last_seen_hex": f"hex_{hex_id}",
            "faction": faction,
            "attitude_to_player": attitude,
            "alive": True
        }
        
        with open(self.npc_persistence_file, "w") as f:
            json.dump(data, f, indent=2)
