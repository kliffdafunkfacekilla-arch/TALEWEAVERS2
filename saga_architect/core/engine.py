"""
Saga Chronos Engine — Full Living World Simulation
Handles the turn-based simulation of Ostraka's living world:
  - Resources (basic + lore-specific)
  - Building construction and upgrade tiers
  - Flora & Fauna ecology (migration, hostility, farmability)
  - Trade routes (internal and external)
  - Unrest and civil strife
  - Crime and banditry
  - Chaos Biome (Convergence + 12 arms, drift, creature spawns)
  - Dragonstone meteor showers during Shadow Week
  - Faction AI: gather, build, fight, expand
"""

import json
import os
import random
import math
from .chronos_clock import ChronosClock

# ── File paths ─────────────────────────────────────────────────────────────
MODULE_DIR     = os.path.dirname(os.path.abspath(__file__))
BASE_DIR       = os.path.dirname(MODULE_DIR)
DATA_DIR       = os.path.join(BASE_DIR, "data")
MODULE_DATA    = os.path.join(MODULE_DIR, "data")   # saga_chronos/data/
MAP_FILE       = os.path.join(DATA_DIR,    "Saga_Master_World.json")
CALENDAR_FILE  = os.path.join(MODULE_DATA, "calendar_rules.json")   # lives in saga_chronos/data/
ENTITIES_FILE  = os.path.join(DATA_DIR,    "entity_rules.json")
SAVE_FILE      = os.path.join(MODULE_DATA, "chronos_save.json")
CHRONICLE_FILE = os.path.join(DATA_DIR,    "Chronicle_Log.json")

# ── Resource type registry──────────────────────────────────────────────────
BASIC_RESOURCES = ["food", "wood", "stone", "iron", "copper", "gold", "nickel", "clay", "hide"]
LORE_RESOURCES  = ["dragonstone", "d_dust", "atherium_coin",
                    "ichor_honey", "voltaic_fleece", "ozone_milk",
                    "lith_weave", "aether_clear", "avian_silk"]
ALL_RESOURCES   = BASIC_RESOURCES + LORE_RESOURCES

def _empty_resources():
    return {r: 0.0 for r in ALL_RESOURCES}

# ── Building tier definitions ──────────────────────────────────────────────
BUILDING_TIERS = [
    {"tier": 0, "name": "Camp",       "buildings": ["hearth", "storage_pit"],                  "unlock": {}},
    {"tier": 1, "name": "Settlement", "buildings": ["farm", "hunting_post", "gather_camp", "dirt_road"],  "unlock": {"food": 50}},
    {"tier": 2, "name": "Town",       "buildings": ["sawmill", "quarry", "watchtower", "dirt_road"],      "unlock": {"wood": 50, "stone": 20}},
    {"tier": 3, "name": "City",       "buildings": ["mine", "iron_forge", "market", "paved_road", "walls"], "unlock": {"iron": 20, "gold": 10}},
    {"tier": 4, "name": "Stronghold", "buildings": ["garrison", "keep", "trade_post", "highway"],         "unlock": {"military_strength": 80}},
    {"tier": 5, "name": "Capital",    "buildings": ["castle", "great_market", "harbour"],               "unlock": {"atherium_coin": 5000}},
]

DEFENSIVE_STRUCTURES = {
    "watchtower":  {"cost": {"stone": 10},             "defense_bonus": 15, "crime_reduction": 0.15, "unrest_reduction": 5},
    "walls":       {"cost": {"stone": 30, "wood": 10}, "defense_bonus": 40, "crime_reduction": 0.05},
    "keep":        {"cost": {"stone": 60, "iron": 20}, "defense_bonus": 80, "unrest_reduction": 15},
    "stronghold":  {"cost": {"stone": 100, "iron": 50, "gold": 20}, "defense_bonus": 150, "crime_immunity": True},
}

# ── Chaos zone definitions (12 arms of the Convergence) ───────────────────
CHAOS_ZONES = [
    {"id": 1,  "name": "The Crushing Lowlands", "magister": "Tiraton",  "spawn_creature": "Press-Beetles",      "warp": "GRAV_DENSE"},
    {"id": 2,  "name": "The Frozen Grid",        "magister": "Stagus",   "spawn_creature": "Fractal-Stalkers",   "warp": "GRID_LOCK"},
    {"id": 3,  "name": "The Kinetic Wastes",     "magister": "Vecelo",   "spawn_creature": "Blitz-Flies",        "warp": "THE_BLUR"},
    {"id": 4,  "name": "The Gilded Bog",         "magister": "Aurgenas", "spawn_creature": "Amorphous-Elk",      "warp": "STATE_DRIFT"},
    {"id": 5,  "name": "The Chimera Veldt",      "magister": "Gavusrix", "spawn_creature": "Poly-Beasts",        "warp": "HYPER_EVOLVE"},
    {"id": 6,  "name": "The Tungsten Hells",     "magister": "Carulkem", "spawn_creature": "Cinder-Simians",     "warp": "EMBER_HIDE"},
    {"id": 7,  "name": "The Magnetic Fog",       "magister": "Metrion",  "spawn_creature": "Lodestone-Wasps",    "warp": "STATIC_BLEACH"},
    {"id": 8,  "name": "The Shifting Veil",      "magister": "Lophex",   "spawn_creature": "Phase-Predators",    "warp": "SPELL_TOUCHED"},
    {"id": 9,  "name": "The Prism Spires",       "magister": "Opecten",  "spawn_creature": "Prism-Ferns",        "warp": "GLASS_GAZE"},
    {"id": 10, "name": "The Rotting Gardens",    "magister": "Termhill", "spawn_creature": "Shadow-Crows",       "warp": "CRYPT_ROT"},
    {"id": 11, "name": "The Euphoric Oasis",     "magister": "Virantor", "spawn_creature": "Dream-Spiders",      "warp": "THE_GLAMOUR"},
    {"id": 12, "name": "The Bedlam Peaks",       "magister": "Tyrustis", "spawn_creature": "Poly-Gons",          "warp": "GUILT_WRACK"},
]


# ═══════════════════════════════════════════════════════════════════════════
class ChronosEngine:
# ═══════════════════════════════════════════════════════════════════════════

    def __init__(self):
        print("[CHRONOS] Initializing World Simulation Engine...")
        self.world_map     = self._load_json(MAP_FILE,       {"macro_map": []})
        self.calendar_cfg  = self._load_json(CALENDAR_FILE,  {"months": [], "seasons": {}})
        self.entity_rules  = self._load_json(ENTITIES_FILE,  {"factions": {}, "wildlife": {}, "flora": {}})
        self.state         = self._load_json(SAVE_FILE,      {"current_tick": 0, "factions": {}, "chaos_arms": {}})
        self.chronicle     = self._load_json(CHRONICLE_FILE, [])
        self.clock         = ChronosClock(self.calendar_cfg)

        # Index map cells by id for fast lookup
        self._hex_index = {str(h.get("id", "")): h for h in self.world_map.get("macro_map", [])}

        # Ensure chaos arm state is initialized
        if "chaos_arms" not in self.state:
            self.state["chaos_arms"] = {}
        for zone in CHAOS_ZONES:
            key = str(zone["id"])
            if key not in self.state["chaos_arms"]:
                self.state["chaos_arms"][key] = {"drift_offset": 0, "active_hexes": []}

        print(f"[CHRONOS] World loaded: {len(self._hex_index)} hexes | Tick {self.state['current_tick']}")

    # ── Persistence ─────────────────────────────────────────────────────────

    def _load_json(self, path, fallback):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[CHRONOS] Warning: could not load {path}: {e}")
        return fallback

    def save_state(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SAVE_FILE,      "w") as f: json.dump(self.state,            f, indent=2)
        with open(MAP_FILE,       "w") as f: json.dump(self.world_map,        f, indent=2)
        with open(CHRONICLE_FILE, "w") as f: json.dump(self.chronicle[-100:], f, indent=2)

    def log_event(self, event_type, description, faction=None, location=None):
        self.chronicle.append({
            "tick":        self.state["current_tick"],
            "type":        event_type,
            "description": description,
            "faction":     faction,
            "location":    location,
        })
        print(f"  [CHRONICLE] {description}")

    # ── Main tick entry point ────────────────────────────────────────────────

    def run_tick(self, days_to_advance=1):
        """Advance the world by N days. The main simulation heartbeat."""
        time_data = self.clock.advance_time(self.state["current_tick"], days_to_advance)
        new_tick  = time_data["new_tick"]
        self.state["current_tick"] = new_tick

        date = self.clock.get_current_date(new_tick)
        if date is None:
            print("[CHRONOS] Warning: calendar returned None for tick", new_tick, "— check calendar_rules.json")
            return {"year": 1, "month": "Unknown", "day": 1, "season": "Spring", "is_shadow_week": False, "chaos_modifier": 1.0, "moon": {"primary": {}, "secondary": {}}}
        chaos_mod = date.get("chaos_modifier", 1.0)

        print(f"\n{'='*50}")
        if date.get("is_shadow_week"):
            print(f" *** SHADOW WEEK — Day {date['day']} *** Year {date['year']}")
            print(f" Chaos Modifier: {chaos_mod} | Moon: Total Eclipse")
        else:
            print(f" Tick {new_tick} | {date['day']} of {date['month']}, Year {date['year']}")
            print(f" Season: {date['season']} | Cruorbus: {date['moon']['primary']['orbital_phase']} [{date['moon']['primary']['color']}]")
            if date.get("active_alignment"):
                print(f" *** CELESTIAL EVENT: {date['active_alignment']} *** ")
            if date["moon"]["secondary"]["nearby"]:
                print(f" *** ERRANITH APPROACHES — Chaos surge imminent! ***")
        print(f"{'='*50}")

        triggers = time_data["sim_triggers"]

        if triggers["local"]:
            self._simulate_daily(date, chaos_mod)

        if triggers["regional"]:
            self._simulate_regional(date, chaos_mod)

        if triggers["global"]:
            self._simulate_global(date, chaos_mod)

        # Shadow Week special processing
        if date.get("is_shadow_week"):
            self._simulate_shadow_week(date)

        self.save_state()
        return date

    # ── Daily simulation (every tick) ───────────────────────────────────────

    def _simulate_daily(self, date, chaos_mod):
        """Runs every day: weather shifts, minor chaos creature movement."""
        for cell in self.world_map.get("macro_map", []):
            if cell.get("is_chaos") and chaos_mod > 1.5:
                # High chaos days: existing chaos creatures move into adjacent hexes
                intensity = cell.get("chaos_intensity", 0.5)
                if random.random() < 0.02 * intensity * chaos_mod:
                    # Simple spread: if faction is adjacent and weak, damage them
                    owner = cell.get("faction_owner", "")
                    if owner and owner in self.state["factions"]:
                        f = self.state["factions"][owner]
                        dmg = random.uniform(1.0, 3.0) * intensity
                        f["resources"]["food"]       = max(0, f["resources"].get("food", 0) - dmg)
                        f["resources"]["population"] = max(0, f["resources"].get("population", 100) - int(dmg * 2))

    # ── Regional simulation (every 7 days) ──────────────────────────────────

    def _simulate_regional(self, date, chaos_mod):
        """Runs weekly: flora growth pulses, fauna movement, local trade."""
        season = date.get("season", "Spring")
        growth_bonus = self.calendar_cfg.get("seasons", {}).get(season, {}).get("food_growth_bonus", 1.0)

        for cell in self.world_map.get("macro_map", []):
            owner = cell.get("faction_owner", "")
            if not owner or owner not in self.state["factions"]:
                continue
            f = self.state["factions"][owner]

            # Farmable flora: yield food if a farm building exists
            if cell.get("farmable_flora") and "farm" in f.get("buildings", []):
                yield_amt = random.uniform(3.0, 8.0) * growth_bonus
                f["resources"]["food"] = f["resources"].get("food", 0) + yield_amt

            # Hostile fauna: reduce food and population
            if cell.get("hostile_fauna"):
                threat = cell.get("fauna_threat", 0.3)
                if random.random() < threat:
                    food_loss = random.uniform(2.0, 6.0)
                    f["resources"]["food"] = max(0, f["resources"].get("food", 0) - food_loss)
                    if f["resources"]["food"] < 10:
                        f["resources"]["population"] = max(0, f["resources"].get("population", 100) - random.randint(1, 5))
                        self.log_event("FAUNA_ATTACK", f"{owner}: hostile fauna raided a settlement, food depleted.", faction=owner, location=str(cell.get("id")))

    # ── Global simulation (every 30 days) ───────────────────────────────────

    def _simulate_global(self, date, chaos_mod):
        """Runs monthly: full faction economy, building, trade, unrest, crime, chaos drift."""
        print("\n[GLOBAL] Processing full world simulation tick...")
        season = date.get("season", "Spring")

        # Map territory ownership
        faction_territories = {}
        for cell in self.world_map.get("macro_map", []):
            owner = cell.get("faction_owner", "")
            if owner:
                faction_territories.setdefault(owner, []).append(cell)

        if not faction_territories:
            print("  -> No factions hold territory. Skipping economy.")
        else:
            # Process each faction
            for faction_name, hexes in faction_territories.items():
                self._process_faction(faction_name, hexes, season, chaos_mod)

        # Trade routes between neighbouring factions
        self._simulate_trade(faction_territories)

        # Crime and banditry
        self._simulate_crime(faction_territories)

        # Chaos Biome drift
        self._simulate_chaos_drift(chaos_mod)

        # Chaos creature spawns
        self._simulate_chaos_spawns(chaos_mod)

        # Emit world events for the Context Assembler
        self._emit_world_events(date)

    # ── Per-faction processing ───────────────────────────────────────────────

    def _process_faction(self, faction_name, hexes, season, chaos_mod):
        # Ensure faction state exists with full resource dict
        if faction_name not in self.state["factions"]:
            self.state["factions"][faction_name] = {
                "resources":         _empty_resources(),
                "population":        1000,
                "military_strength": 50.0,
                "buildings":         ["hearth", "storage_pit"],
                "tier":              0,
                "unrest":            0,
                "at_war_with":       [],
                "trade_routes":      [],
                "regional_structures": {}, # hex_id -> { "rx,ry": [buildings] }
            }
            self.state["factions"][faction_name]["resources"]["food"] = 200.0

        f = self.state["factions"][faction_name]
        r = f["resources"]
        season_rules   = self.calendar_cfg.get("seasons", {}).get(season, {})
        food_bonus     = season_rules.get("food_growth_bonus", 1.0)
        is_winter      = (season == "Winter")

        # ── Resource gathering from territory ────────────────────────────
        for cell in hexes:
            local_res = cell.get("local_resources", [])
            for res in local_res:
                key = res.lower().replace("-", "_").replace(" ", "_")
                if key in r:
                    yield_amt = random.uniform(5.0, 15.0)
                    # Dragonstone only from chaos-adjacent hexes
                    if key == "dragonstone" and not cell.get("chaos_adjacent"):
                        yield_amt *= 0.1
                    r[key] = r.get(key, 0) + yield_amt

            # Basic gathering from biome type
            biome = cell.get("biome_type", "grassland")
            if not cell.get("is_chaos"):
                r["food"]  = r.get("food", 0)  + random.uniform(2, 6) * food_bonus
                r["wood"]  = r.get("wood", 0)  + (random.uniform(3, 8) if biome in ["forest", "jungle"] else random.uniform(0.5, 2))
                r["stone"] = r.get("stone", 0) + (random.uniform(2, 5) if biome in ["mountain", "rocky", "volcano"] else random.uniform(0.2, 1))
                r["iron"]  = r.get("iron", 0)  + (random.uniform(1, 3) if biome in ["mountain", "volcano"] else 0)
                r["gold"]  = r.get("gold", 0)  + (random.uniform(0.1, 0.5) if biome in ["mountain", "river", "alluvial"] else 0)
                r["clay"]  = r.get("clay", 0)  + (random.uniform(1, 4) if biome in ["river", "swamp"] else 0)
                if "hunting_post" in f["buildings"]:
                    r["hide"] = r.get("hide", 0) + random.uniform(1, 3)

        # ── Food consumption ─────────────────────────────────────────────
        pop = f.get("population", 1000)
        food_burn = (pop / 200.0) * (1.3 if is_winter else 1.0)
        r["food"] = max(0.0, r.get("food", 0) - food_burn)

        # ── Starvation ───────────────────────────────────────────────────
        is_starving = r["food"] < 20.0
        if is_starving:
            f["population"]        = max(0, int(pop * 0.97))
            f["military_strength"] = max(0.0, f.get("military_strength", 50) - random.uniform(2, 5))
            f["unrest"]            = min(100, f.get("unrest", 0) + 15)
            self.log_event("STARVATION", f"{faction_name} is starving! Population and military declining.", faction=faction_name)

        # ── Population growth (when not starving) ────────────────────────
        if not is_starving and r["food"] > 100:
            f["population"] = int(pop * 1.02)

        # ── Building construction ─────────────────────────────────────────
        self._try_build(faction_name, f, r)

        # ── Military: recover when fed, attrition in war ─────────────────
        if not is_starving:
            f["military_strength"] = min(100.0, f.get("military_strength", 50) + random.uniform(0.5, 2.0))

        for enemy in list(f.get("at_war_with", [])):
            if enemy in self.state["factions"]:
                attrition = random.uniform(3, 8) * chaos_mod
                f["military_strength"]                                  = max(0, f["military_strength"] - attrition)
                self.state["factions"][enemy]["military_strength"]       = max(0, self.state["factions"][enemy]["military_strength"] - attrition)
                if f["military_strength"] < 5 or self.state["factions"][enemy]["military_strength"] < 5:
                    f["at_war_with"].remove(enemy)
                    self.state["factions"][enemy]["at_war_with"] = [x for x in self.state["factions"][enemy].get("at_war_with", []) if x != faction_name]
                    self.log_event("WAR_ENDED", f"War between {faction_name} and {enemy} concluded through attrition.", faction=faction_name)

        # ── Unrest decay (good conditions reduce it) ─────────────────────
        if not is_starving and "market" in f["buildings"]:
            f["unrest"] = max(0, f.get("unrest", 0) - 10)
        if "watchtower" in f["buildings"]:
            f["unrest"] = max(0, f.get("unrest", 0) - 5)

        # ── Civil uprising at extreme unrest ──────────────────────────────
        if f.get("unrest", 0) >= 90:
            f["military_strength"] = max(0, f["military_strength"] - 10)
            self.log_event("UPRISING", f"{faction_name} suffers a civil uprising! Military weakened.", faction=faction_name)

        # ── D-Dust production from Dragonstone ───────────────────────────
        if r.get("dragonstone", 0) > 10:
            dust_yield = r["dragonstone"] * 0.3
            r["d_dust"]       = r.get("d_dust", 0) + dust_yield
            r["dragonstone"] -= dust_yield  # milling consumes raw stone

        # ── Print monthly report ──────────────────────────────────────────
        print(f"  [{faction_name}] Pop:{f['population']} | Mil:{f['military_strength']:.1f} | "
              f"Tier:{f['tier']} | Food:{r['food']:.0f} | Gold:{r['gold']:.1f} | "
              f"Dragonstone:{r['dragonstone']:.1f} | Unrest:{f.get('unrest',0)}")

    # ── Building construction logic ──────────────────────────────────────────

    def _try_build(self, name, f, r):
        current_tier = f.get("tier", 0)
        next_tier    = current_tier + 1
        if next_tier >= len(BUILDING_TIERS):
            return

        required = BUILDING_TIERS[next_tier]["unlock"]
        can_build = True
        for res, amount in required.items():
            if res == "military_strength":
                if f.get("military_strength", 0) < amount:
                    can_build = False
                    break
            else:
                if r.get(res, 0) < amount:
                    can_build = False
                    break

        if can_build:
            # Spend resources
            for res, amount in required.items():
                if res != "military_strength":
                    r[res] = max(0, r.get(res, 0) - amount)

            f["tier"] = next_tier
            tier_info = BUILDING_TIERS[next_tier]
            f["buildings"] = list(set(f.get("buildings", []) + tier_info["buildings"]))
            
            # Place new buildings in a Regional Space (20x20)
            # Pick a hex they own
            owned_hexes = [h for h in self.world_map.get("macro_map", []) if h.get("faction_owner") == name]
            if owned_hexes:
                target_hex = random.choice(owned_hexes)
                hex_id = str(target_hex["id"])
                rx, ry = random.randint(0, 19), random.randint(0, 19)
                f_structs = f.setdefault("regional_structures", {})
                hex_structs = f_structs.setdefault(hex_id, {})
                coord_key = f"{rx},{ry}"
                hex_structs.setdefault(coord_key, []).extend(tier_info["buildings"])
                
            self.log_event("BUILD", f"{name} upgraded to Tier {next_tier}: {tier_info['name']} — built {', '.join(tier_info['buildings'])}.", faction=name)

        # Also try to build defensive structures if stone/iron available
        for structure, data in DEFENSIVE_STRUCTURES.items():
            if structure not in f.get("buildings", []):
                costs = data["cost"]
                if all(r.get(res, 0) >= qty for res, qty in costs.items()):
                    for res, qty in costs.items():
                        r[res] = max(0, r.get(res, 0) - qty)
                    f["buildings"].append(structure)
                    f["unrest"]           = max(0, f.get("unrest", 0) - data.get("unrest_reduction", 0))
                    f["military_strength"] = min(100, f.get("military_strength", 50) + data.get("defense_bonus", 0) * 0.1)
                    self.log_event("BUILD", f"{name} constructed a {structure}.", faction=name)

    # ── Trade routes ─────────────────────────────────────────────────────────

    def _simulate_trade(self, faction_territories):
        """Monthly trade between neighbouring factions that are not at war."""
        processed = set()
        for f_name, hexes in faction_territories.items():
            f_state = self.state["factions"].get(f_name, {})
            for other_name, other_hexes in faction_territories.items():
                if other_name == f_name or (f_name, other_name) in processed:
                    continue
                o_state = self.state["factions"].get(other_name, {})
                if other_name in f_state.get("at_war_with", []):
                    continue

                # Check adjacency (simplified: assume factions with hexes share borders if both exist)
                # In full impl, compare hex coordinates
                trade_vol = random.uniform(5.0, 20.0)
                # Each faction gives its surplus resource
                for res in BASIC_RESOURCES:
                    f_surplus = f_state.get("resources", {}).get(res, 0) - 50
                    o_surplus = o_state.get("resources", {}).get(res, 0) - 50
                    if f_surplus > 0 and o_surplus < 0:
                        transfer = min(f_surplus, trade_vol)
                        f_state["resources"][res]  = max(0, f_state["resources"].get(res, 0) - transfer)
                        o_state["resources"][res]  = o_state["resources"].get(res, 0) + transfer
                        # Both earn a little gold from trade taxes
                        f_state["resources"]["gold"] = f_state["resources"].get("gold", 0) + transfer * 0.05
                        o_state["resources"]["gold"] = o_state["resources"].get("gold", 0) + transfer * 0.05

                processed.add((f_name, other_name))
                processed.add((other_name, f_name))

    # ── Crime and banditry ───────────────────────────────────────────────────

    def _simulate_crime(self, faction_territories):
        """Monthly crime check on trade routes. Spawns bandit factions if left unchecked."""
        for f_name, hexes in faction_territories.items():
            f_state = self.state["factions"].get(f_name, {})
            has_watchtower  = "watchtower"  in f_state.get("buildings", [])
            has_stronghold  = "stronghold"  in f_state.get("buildings", [])

            if has_stronghold:
                continue  # Strongholds grant full crime immunity

            base_risk = 0.2
            risk = base_risk * (0.25 if has_watchtower else 1.0)

            if random.random() < risk:
                # Caravan raided: lose some gold and food
                gold_loss = random.uniform(2, 8)
                food_loss = random.uniform(5, 15)
                f_state["resources"]["gold"] = max(0, f_state["resources"].get("gold", 0) - gold_loss)
                f_state["resources"]["food"] = max(0, f_state["resources"].get("food", 0) - food_loss)
                f_state["unrest"] = min(100, f_state.get("unrest", 0) + 5)
                self.log_event("CRIME", f"{f_name}: a trade caravan was raided! Lost {gold_loss:.1f} gold and {food_loss:.1f} food.", faction=f_name)

                # Chance to spawn a bandit faction
                if random.random() < 0.15 and "BANDITS" not in self.state["factions"]:
                    self.state["factions"]["BANDITS"] = {
                        "resources":         _empty_resources(),
                        "population":        50,
                        "military_strength": 20.0,
                        "buildings":         ["camp"],
                        "tier":              0,
                        "unrest":            0,
                        "at_war_with":       [],
                    }
                    self.state["factions"]["BANDITS"]["resources"]["food"] = 30.0
                    self.log_event("BANDIT_SPAWN", f"A bandit clan emerged near {f_name} territory!", faction="BANDITS")

    # ── Chaos Biome drift ────────────────────────────────────────────────────

    def _simulate_chaos_drift(self, chaos_mod):
        """Monthly: outer edges of each Chaos Arm shift ±1 hex randomly."""
        print("[CHAOS] Simulating Convergence drift...")
        for zone in CHAOS_ZONES:
            key = str(zone["id"])
            arm = self.state["chaos_arms"][key]

            # Drift amount scales with chaos modifier (worst during Open Eye / Shadow Week)
            drift = random.choice([-1, 0, 0, 1])  # Mostly stable, occasional shift
            if chaos_mod > 2.0:
                drift = random.choice([-1, 0, 1, 1])  # More drift during surges

            arm["drift_offset"] = arm.get("drift_offset", 0) + drift

            # Apply drift to world map: update chaos hex borders
            # We tag hexes at the arm's current fringe
            new_hex_ids = self._compute_chaos_arm_hexes(zone["id"], arm["drift_offset"])
            old_hex_ids = set(arm.get("active_hexes", []))
            new_hex_set = set(new_hex_ids)

            # Hexes newly swallowed by chaos
            for hex_id in new_hex_set - old_hex_ids:
                cell = self._hex_index.get(hex_id, {})
                if cell:
                    cell["is_chaos"]        = True
                    cell["chaos_zone"]       = zone["name"]
                    cell["chaos_intensity"]  = 0.4  # New hexes start at fringe intensity
                    cell["dragonstone_deposit"] = random.random() < 0.3
                    # Damage the faction that owned it
                    owner = cell.get("faction_owner", "")
                    if owner and owner in self.state["factions"]:
                        f = self.state["factions"][owner]
                        f["resources"]["population"] = max(0, f["resources"].get("population", 100) * 0.5)
                        f["resources"]["food"]        = max(0, f["resources"].get("food", 0) * 0.7)
                        f["unrest"]                   = min(100, f.get("unrest", 0) + 30)
                        self.log_event("CHAOS_DRIFT", f"Chaos arm '{zone['name']}' engulfed a hex owned by {owner}! Population and food devastated.", faction=owner, location=hex_id)

            # Hexes freed from chaos
            for hex_id in old_hex_ids - new_hex_set:
                cell = self._hex_index.get(hex_id, {})
                if cell:
                    cell.pop("is_chaos",        None)
                    cell.pop("chaos_zone",       None)
                    cell.pop("chaos_intensity",  None)
                    cell["dragonstone_residue"]  = True   # Bonus resource for 3 ticks
                    self.log_event("CHAOS_FREED", f"A hex retreated from chaos zone '{zone['name']}' — Dragonstone residue remains.", location=hex_id)

            arm["active_hexes"] = list(new_hex_set)

    def _compute_chaos_arm_hexes(self, zone_id, drift_offset):
        """
        Computes the list of hex IDs that belong to this arm given its current drift.
        Uses a radial line from the map centre outward at 30° × (zone_id-1),
        then applies the drift as a lateral offset perpendicular to the arm direction.
        This is an approximation based on hex ID numeric ranges available.
        In production, actual hex coordinates from the map are used.
        """
        # Placeholder: return a fixed stub set until we have real coordinate data
        # Replace with real hex grid math once the map coordinate system is confirmed
        base_ids = [f"{zone_id * 100 + i}" for i in range(20)]
        return base_ids

    # ── Chaos creature spawns ────────────────────────────────────────────────

    def _simulate_chaos_spawns(self, chaos_mod):
        """Monthly: chaos hexes have a chance to spawn creatures that spread outward."""
        for cell in self.world_map.get("macro_map", []):
            if not cell.get("is_chaos"):
                continue

            intensity     = cell.get("chaos_intensity", 0.5)
            spawn_chance  = 0.05 + (intensity * 0.25 * chaos_mod * 0.5)
            spawn_chance  = min(spawn_chance, 0.5)  # Cap at 50%

            if random.random() < spawn_chance:
                zone_name = cell.get("chaos_zone", "Unknown")
                zone_def  = next((z for z in CHAOS_ZONES if z["name"] == zone_name), None)
                creature  = zone_def["spawn_creature"] if zone_def else "Chaos-Beast"

                # Find the adjacent non-chaos hex (simplified: any neighbouring faction hex)
                owner = cell.get("faction_owner", "")
                if owner and owner in self.state["factions"]:
                    f = self.state["factions"][owner]
                    food_dmg = random.uniform(3, 10) * intensity
                    f["resources"]["food"]        = max(0, f["resources"].get("food", 0) - food_dmg)
                    f["resources"]["population"]  = max(0, f["resources"].get("population", 100) - random.randint(2, 8))
                    self.log_event("CHAOS_SPAWN", f"A {creature} emerged from '{zone_name}' and attacked {owner} settlements!", faction=owner, location=str(cell.get("id")))

                    # Military can clear it (at cost)
                    if f.get("military_strength", 0) > 30:
                        kill_roll = random.random()
                        if kill_roll > 0.4:
                            f["military_strength"] = max(0, f["military_strength"] - random.uniform(3, 8))
                            # Dragonstone drop from slain creature
                            f["resources"]["dragonstone"] = f["resources"].get("dragonstone", 0) + random.uniform(1, 5)
                            self.log_event("CREATURE_SLAIN", f"{owner} forces slew the {creature} — recovered Dragonstone!", faction=owner)

    # ── Shadow Week processing ───────────────────────────────────────────────

    def _simulate_shadow_week(self, date):
        """
        Shadow Week (7-day eclipse at year end):
        - Avian Empire mints Aetherium Coin
        - Dragonstone meteor shower rains down on random hexes
        - Chaos tides devastate coastal hexes
        - Each faction performs their cultural response
        """
        print("[SHADOW WEEK] Processing annual eclipse events...")

        # Only process full Shadow Week once per year (on its first day)
        if date.get("day") != 1:
            return

        # ── Aetherium minting (Avian Empire only) ─────────────────────────
        for f_name, f_state in self.state["factions"].items():
            if "avian" in f_name.lower() or "empire" in f_name.lower():
                dust = f_state["resources"].get("d_dust", 0)
                coins_minted = dust * 10
                f_state["resources"]["atherium_coin"] = f_state["resources"].get("atherium_coin", 0) + coins_minted
                f_state["resources"]["d_dust"]         = 0
                self.log_event("SHADOW_WEEK", f"Avian Empire minted {coins_minted:.0f} Aetherium Coins from d_dust reserves!", faction=f_name)

        # ── Meteor shower: Dragonstone rains down ─────────────────────────
        meteor_hexes = random.sample(list(self._hex_index.keys()), k=min(10, len(self._hex_index)))
        for hex_id in meteor_hexes:
            cell = self._hex_index.get(hex_id, {})
            if cell:
                cell["dragonstone_deposit"] = True
                owner = cell.get("faction_owner", "")
                if owner and owner in self.state["factions"]:
                    yield_amt = random.uniform(10, 40)
                    self.state["factions"][owner]["resources"]["dragonstone"] = \
                        self.state["factions"][owner]["resources"].get("dragonstone", 0) + yield_amt
                    self.log_event("METEOR_SHOWER", f"Dragonstone meteor fell in {owner} territory — {yield_amt:.0f} Dragonstone recovered!", faction=owner, location=hex_id)

        # ── Chaos tide: coastal factions take damage ───────────────────────
        for f_name, f_state in self.state["factions"].items():
            # Check if faction has coastal hexes (simplified: biome check)
            for cell in self.world_map.get("macro_map", []):
                if cell.get("faction_owner") == f_name and cell.get("biome_type") in ["coast", "ocean", "sea", "river"]:
                    dmg = random.uniform(10, 30)
                    f_state["resources"]["food"] = max(0, f_state["resources"].get("food", 0) - dmg)
                    f_state["unrest"] = min(100, f_state.get("unrest", 0) + 10)
                    self.log_event("SHADOW_TIDE", f"Chaos tides battered {f_name} coastal settlements during Shadow Week!", faction=f_name)
                    break  # One tide event per faction

    # ── World events emission ────────────────────────────────────────────────

    def _emit_world_events(self, date):
        """
        Called at end of each global tick. Writes data/world_events.json.
        Translates monthly sim state into the NPC schedules, caravan routes,
        patrol paths, and bandit threats that the Context Assembler uses to
        populate the player's immediate game world.

        Each event includes:
          - known_by: factions who know this event at the current tick
          - carrier_npcs: event IDs of moving NPCs who carry this news
          - rumour_text: human-readable text for NPC dialogue
        """
        WORLD_EVENTS_FILE = os.path.join(DATA_DIR, "world_events.json")

        events    = []
        evt_index = {}   # id → event, for cross-referencing carrier_npcs
        evt_counter = [0]

        def next_id():
            evt_counter[0] += 1
            return f"evt_{evt_counter[0]:04d}"

        tick    = self.state["current_tick"]
        month   = date.get("month", "Unknown")
        season  = date.get("season", "Spring")
        hexes   = self.world_map.get("macro_map", [])
        
        # Helper to get a random Regional coord for a hex
        def get_rand_rxry():
            return random.randint(0, 19), random.randint(0, 19)

        # ── 1. Trade caravans ─────────────────────────────────────────────
        # Each active trade route from _simulate_trade generates a caravan NPC
        faction_names = list(self.state["factions"].keys())
        processed_pairs = set()
        for i, f_name in enumerate(faction_names):
            f_state = self.state["factions"].get(f_name, {})
            if f_state.get("tier", 0) < 1:
                continue   # Only settled factions run caravans

            for j, other_name in enumerate(faction_names):
                if i >= j or other_name in f_state.get("at_war_with", []):
                    continue
                pair_key = (f_name, other_name)
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                # 4-Layer Hierarchy
                origin_hex_ids = [h["id"] for h in hexes if h.get("faction_owner") == f_name]
                caravan = {
                    "id":           eid,
                    "type":         "TRADE_CARAVAN",
                    "faction":      f_name,
                    "destination_faction": other_name,
                    "goods":        goods,
                    "npc_name":     npc_name,
                    "npc_type":     "Merchant",
                    "departs_tick": depart_day,
                    "arrives_tick": arrive_day,
                    "total_days":   travel_days,
                    "day_phase_active": ["MORNING", "AFTERNOON"],   # Travels by day
                    "home_tick":    arrive_day + 5,   # Back at origin 5 days after delivery
                    # 4-Layer Hierarchy
                    "hex":          f"hex_{random.choice(origin_hex_ids) if origin_hex_ids else '1'}",
                    "rx":           random.randint(0, 19),
                    "ry":           random.randint(0, 19),
                    # Carrier propagation
                    "known_by":    [f_name, other_name],
                    "carrier_npcs": [],
                    "rumour_text": (f"A merchant wagon from {f_name} is travelling to "
                                    f"{other_name} carrying {', '.join(goods) if goods else 'trade goods'}."),
                    "major_event": False,
                }
                events.append(caravan)
                evt_index[eid] = caravan

        # ── 2. Patrol routes ──────────────────────────────────────────────
        for f_name, f_state in self.state["factions"].items():
            if "watchtower" not in f_state.get("buildings", []) and f_state.get("tier", 0) < 2:
                continue

            eid      = next_id()
            patrol   = {
                "id":         eid,
                "type":       "PATROL_ROUTE",
                "faction":    f_name,
                "npc_name":   f"{f_name} Patrol",
                "npc_type":   "Guard",
                "frequency":  "daily",
                "day_phase_active": ["DAWN", "MORNING", "AFTERNOON", "EVENING"],
                "night_rest_location": "faction_headquarters",
                "military_strength":  f_state.get("military_strength", 30),
                # 4-Layer Hierarchy
                "hex":          f"hex_{random.choice([h['id'] for h in hexes if h.get('faction_owner') == f_name]) if any(h.get('faction_owner') == f_name for h in hexes) else '1'}",
                "rx":           random.randint(0, 19),
                "ry":           random.randint(0, 19),
                # Carrier propagation
                "known_by":    [f_name],
                "carrier_npcs": [],
                "rumour_text": f"{f_name} patrols are active on the roads near their territory.",
                "major_event": False,
            }
            events.append(patrol)
            evt_index[eid] = patrol

        # ── 3. Bandit camps ───────────────────────────────────────────────
        if "BANDITS" in self.state["factions"]:
            b = self.state["factions"]["BANDITS"]
            eid = next_id()
            # Find adjacent victims to set threat area
            victims = [f for f in faction_names if f != "BANDITS"]
            known_by = victims[:2] if victims else []    # Only nearby factions know

            bandit_evt = {
                "id":            eid,
                "type":          "BANDIT_CAMP",
                "faction":       "BANDITS",
                "npc_name":      "Bandit Warband",
                "npc_type":      "Bandit",
                "strength":      int(b.get("military_strength", 20)),
                "threat_radius": 2,
                "day_phase_active": ["AFTERNOON", "EVENING", "NIGHT"],
                "known_by":      known_by,
                "carrier_npcs":  [],
                "rumour_text":   "Word has spread of bandit activity in the wilderness. Merchants travel uneasily.",
                "major_event":   b.get("military_strength", 0) > 60,  # Major if powerful bandits
            }
            events.append(bandit_evt)
            evt_index[eid] = bandit_evt

        # ── 4. Chaos surge events ─────────────────────────────────────────
        chaos_mod = date.get("chaos_modifier", 1.0)
        if chaos_mod >= 1.8:   # Summer Open Eye or worse
            moon_info   = date.get("moon", {}).get("primary", {})
            eid         = next_id()
            alignment   = date.get("active_alignment")

            chaos_evt = {
                "id":          eid,
                "type":        "CHAOS_SURGE",
                "moon_phase":  moon_info.get("orbital_phase", "Unknown"),
                "moon_color":  moon_info.get("color", "Red"),
                "alignment":   alignment,
                "chaos_modifier": chaos_mod,
                "npc_type":    "Chaos Creature",
                "day_phase_active": ["NIGHT", "DAWN"],    # Chaos strongest at night
                "known_by":    faction_names,              # Everyone can see the red moon
                "carrier_npcs": [],
                "rumour_text": (
                    f"The Broken Moon burns {moon_info.get('color','Red')} in the sky. "
                    f"Wardens have gone to high alert. {'The ' + alignment + ' is upon us.' if alignment else ''}"
                ),
                "major_event": True,    # Red moon = everyone knows immediately
            }
            events.append(chaos_evt)
            evt_index[eid] = chaos_evt

        # ── 5. War declarations ───────────────────────────────────────────
        for f_name, f_state in self.state["factions"].items():
            for enemy_name in f_state.get("at_war_with", []):
                eid = next_id()
                war_evt = {
                    "id":        eid,
                    "type":      "WAR",
                    "faction":   f_name,
                    "enemy":     enemy_name,
                    "tick":      tick,
                    "npc_type":  "Soldier",
                    "day_phase_active": ["MORNING", "AFTERNOON"],
                    "known_by":  faction_names,   # Wars are major — everyone hears
                    "carrier_npcs": [],
                    "rumour_text": f"War has erupted between {f_name} and {enemy_name}. Roads are dangerous.",
                    "major_event": True,
                }
                events.append(war_evt)
                evt_index[eid] = war_evt

        # ── 6. Carrier cross-linking ──────────────────────────────────────
        # Trade caravans carry news about events they would have witnessed
        # i.e. events tagged to factions the caravan knows about (same known_by overlap)
        caravan_evts = [e for e in events if e["type"] == "TRADE_CARAVAN"]
        non_caravan  = [e for e in events if e["type"] != "TRADE_CARAVAN"]
        for news_evt in non_caravan:
            for caravan in caravan_evts:
                # Caravan carries the news if its origin faction knows about the event
                if caravan["faction"] in news_evt.get("known_by", []):
                    if caravan["id"] not in news_evt["carrier_npcs"]:
                        news_evt["carrier_npcs"].append(caravan["id"])
                        news_evt["known_by"] = list(set(
                            news_evt["known_by"] + [caravan["destination_faction"]]
                        ))

        # ── Write output ──────────────────────────────────────────────────
        output = {
            "generated_tick": tick,
            "month":          month,
            "season":         season,
            "chaos_modifier": chaos_mod,
            "events":         events,
        }

        os.makedirs(DATA_DIR, exist_ok=True)
        with open(WORLD_EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"[WORLD EVENTS] Emitted {len(events)} events to world_events.json")
        return events


# ── CLI entry point for testing ────────────────────────────────────────────
if __name__ == "__main__":
    engine = ChronosEngine()
    # Simulate 30 days to trigger the first global tick
    result = engine.run_tick(days_to_advance=30)
    print(f"\nDate: {result['day']} of {result['month']}, Year {result['year']}")
    print(f"Season: {result['season']} | Chaos Modifier: {result['chaos_modifier']}")
