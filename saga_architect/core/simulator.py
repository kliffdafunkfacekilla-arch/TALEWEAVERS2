"""
Saga Architect - World Simulation Engine
Handles the turn-based tick logic for the living world:
- Faction expansion / starvation
- Population changes per hex
- Seasonal cycle tracking
- JSON export for the Campaign Weaver to read
"""

import json
import random
from typing import List, Dict
from core.schemas import FactionState, WorldSnapshot, HexOverride


SEASONS = ["SPRING", "SUMMER", "AUTUMN", "WINTER"]


def _next_season(current: str) -> tuple[str, int]:
    """Advance season, return (new_season, year_delta)."""
    idx = SEASONS.index(current) if current in SEASONS else 0
    next_idx = (idx + 1) % 4
    year_delta = 1 if next_idx == 0 else 0
    return SEASONS[next_idx], year_delta


def apply_events_to_state(snapshot: WorldSnapshot, events: List[dict]) -> WorldSnapshot:
    """
    Inject player Chronicle Ledger events into world state before ticking.
    Each event has: location_hex_id, event_description.
    """
    for ev in events:
        hex_id = str(ev.get("location_hex_id", "")) if ev.get("location_hex_id") else None
        desc = (ev.get("event_description") or "").lower()

        if hex_id:
            override = snapshot.hex_overrides.get(hex_id, {})
            # Player disruption: reduce threat level and population
            if "routed" in desc or "defeated" in desc or "slain" in desc:
                override["threat_level"] = max(0.0, override.get("threat_level", 50.0) - 30.0)
                override["population"] = max(0, int(override.get("population", 100) * 0.85))
            # Player aid: boost resources
            if "aided" in desc or "supplied" in desc or "protected" in desc:
                override["resource_level"] = min(100.0, override.get("resource_level", 50.0) + 20.0)
            snapshot.hex_overrides[hex_id] = override

        # Faction-level feedback
        associated = ev.get("associated_faction")
        if associated:
            for faction in snapshot.factions:
                if faction.name.lower() == associated.lower():
                    if "routed" in desc or "defeated" in desc:
                        faction.military_strength = max(0.0, faction.military_strength - 25.0)
                    if "slain" in desc and "leader" in desc:
                        faction.military_strength = max(0.0, faction.military_strength - 40.0)
                        faction.is_expanding = False

    return snapshot


def simulate_tick(snapshot: WorldSnapshot) -> WorldSnapshot:
    """
    Execute one simulation tick on the world state.
    Advances faction hunger, conflict, expansion, and seasonal cycle.
    """
    # --- Seasonal Advance ---
    # Each tick = ~1 month in-world
    # Track ticks within a year (4 seasons * 3 = 12 months)
    ticks_per_season = 3
    season_tick = snapshot.tick_count % ticks_per_season
    if season_tick == ticks_per_season - 1:
        new_season, year_delta = _next_season(snapshot.season)
        snapshot.season = new_season
        snapshot.year += year_delta

    snapshot.tick_count += 1
    is_winter = snapshot.season == "WINTER"
    is_summer = snapshot.season == "SUMMER"

    # --- Faction Simulation ---
    for faction in snapshot.factions:
        # Food depletion: faster in winter, slower in summer
        food_burn = random.uniform(8.0, 15.0) if is_winter else random.uniform(3.0, 8.0)
        faction.food_supply = max(0.0, faction.food_supply - food_burn)
        faction.is_starving = faction.food_supply < 20.0

        # Starvation causes military attrition and aggression
        if faction.is_starving:
            faction.military_strength = max(0.0, faction.military_strength - random.uniform(2.0, 6.0))
            # Starving factions become aggressive and start wars
            if faction.military_strength > 30.0 and random.random() < 0.25:
                # Find a neighbour to pick a fight with
                potential_enemies = [
                    f.id for f in snapshot.factions
                    if f.id != faction.id and f.id not in faction.at_war_with
                ]
                if potential_enemies:
                    target_id = random.choice(potential_enemies)
                    if target_id not in faction.at_war_with:
                        faction.at_war_with.append(target_id)
                        print(f"[SIM] {faction.name} declares war due to starvation!")

        # Strong factions expand in spring/summer
        if not faction.is_starving and faction.military_strength > 70.0 and is_summer:
            faction.is_expanding = True
            # Small food gain from expansion (foraging)
            faction.food_supply = min(100.0, faction.food_supply + random.uniform(5.0, 12.0))
        else:
            faction.is_expanding = False

        # Military recovery when not at war and not starving
        if not faction.is_starving and not faction.at_war_with:
            faction.military_strength = min(100.0, faction.military_strength + random.uniform(1.0, 3.0))

        # Resolve ongoing wars - attrition on both sides
        for enemy_id in list(faction.at_war_with):
            enemy = next((f for f in snapshot.factions if f.id == enemy_id), None)
            if enemy:
                faction.military_strength = max(0.0, faction.military_strength - random.uniform(3.0, 8.0))
                enemy.military_strength = max(0.0, enemy.military_strength - random.uniform(3.0, 8.0))
                # War ends if one side collapses
                if faction.military_strength < 10.0 or enemy.military_strength < 10.0:
                    faction.at_war_with = [x for x in faction.at_war_with if x != enemy_id]
                    if faction.id in enemy.at_war_with:
                        enemy.at_war_with = [x for x in enemy.at_war_with if x != faction.id]
                    print(f"[SIM] War between {faction.name} and {enemy.name} has concluded!")

    return snapshot


def export_to_json(snapshot: WorldSnapshot, base_map_path: str, output_path: str):
    """
    Merge simulation state onto the base map JSON and write to output_path.
    The Campaign Weaver reads output_path to ground story generation.
    """
    base_data = {}
    try:
        with open(base_map_path, "r") as f:
            base_data = json.load(f)
    except Exception:
        base_data = {"metadata": {}, "macro_map": []}

    # Enrich the metadata with living sim state
    base_data["sim_metadata"] = {
        "tick_count": snapshot.tick_count,
        "year": snapshot.year,
        "season": snapshot.season,
        "campaign_id": snapshot.campaign_id,
    }

    # Inject faction summaries
    base_data["factions"] = []
    for f in snapshot.factions:
        base_data["factions"].append({
            "id": f.id,
            "name": f.name,
            "type": f.faction_type,
            "military_strength": round(f.military_strength, 1),
            "food_supply": round(f.food_supply, 1),
            "is_starving": f.is_starving,
            "is_expanding": f.is_expanding,
            "at_war_with": f.at_war_with,
            "territory_hex_ids": f.territory_hex_ids,
        })

    # Apply hex overrides to the map cells
    if "macro_map" in base_data:
        for cell in base_data["macro_map"]:
            hex_id = str(cell.get("id", ""))
            if hex_id in snapshot.hex_overrides:
                cell.update(snapshot.hex_overrides[hex_id])

    with open(output_path, "w") as f:
        json.dump(base_data, f, indent=2)

    print(f"[ARCHITECT] World state exported to {output_path}")
