import json
import os
from chronos_clock import ChronosClock

# File Paths - Centralizing to root /data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")
CALENDAR_FILE = os.path.join(DATA_DIR, "calendar_rules.json")
ENTITIES_FILE = os.path.join(DATA_DIR, "entity_rules.json")
SAVE_STATE_FILE = os.path.join(DATA_DIR, "chronos_save.json")
CHRONICLE_FILE = os.path.join(DATA_DIR, "Chronicle_Log.json")

class ChronosEngine:
    def __init__(self):
        print("Initializing Chronos Engine...")
        self.world_map = self._load_json(MAP_FILE, {"macro_map": []})
        self.calendar_config = self._load_json(CALENDAR_FILE, {"months": [], "seasons": {}})
        self.entity_rules = self._load_json(ENTITIES_FILE, {"factions": {}, "resources": {}, "wildlife": {}})
        self.state = self._load_json(SAVE_STATE_FILE, {"current_tick": 0, "factions": {}})
        self.chronicle = self._load_json(CHRONICLE_FILE, [])
        
        # Ensure default calendar exists if nothing was loaded
        if not self.calendar_config.get("months"):
            self.calendar_config = {
              "months": [
                {"name": "Dawnspire", "days": 32, "season": "Spring"},
                {"name": "The_Long_Dark", "days": 40, "season": "Winter"}
              ],
              "seasons": {
                "Spring": { "temp_band": "MID", "precipitation_chance": 0.4, "weather_type": "Rain" },
                "Winter": { "temp_band": "LOW", "precipitation_chance": 0.6, "weather_type": "Snow" }
              },
              "moons": [{"name": "Aetheris", "color": "Pale Blue"}],
              "days_of_week": ["Firstday", "Midday", "Restday"]
            }

        self.clock = ChronosClock(self.calendar_config)

    def _load_json(self, filepath, fallback):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        return fallback

    def save_state(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SAVE_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
        # We also overwrite the map in case borders expanded or resources depleted
        with open(MAP_FILE, 'w') as f:
            json.dump(self.world_map, f, indent=2)
        # Save Chronicle
        with open(CHRONICLE_FILE, 'w') as f:
            json.dump(self.chronicle[-50:], f, indent=2) # Keep last 50 events

    def log_event(self, tick, event_type, description, location=None):
        """ Appends a story event to the Chronicle. """
        event = {
            "tick": tick,
            "type": event_type,
            "description": description,
            "location": location
        }
        self.chronicle.append(event)
        print(f" [CHRONICLE] {description}")

    def run_tick(self, days_to_advance=1):
        """ Press 'Play' on the universe for X days. """
        time_data = self.clock.advance_time(self.state["current_tick"], days_to_advance)
        new_tick = time_data["new_tick"]
        self.state["current_tick"] = new_tick
        
        current_date = self.clock.get_current_date(new_tick)
        
        print(f"\n{'='*40}")
        print(f" DAY {new_tick} | {current_date['day']} of {current_date['month']}, Year {current_date['year']}")
        print(f" Season: {current_date['season']} | Moon: {current_date['moon']['phase']}")
        print(f"{'='*40}")

        # Execute the Simulation Tiers
        if time_data["sim_triggers"]["local"]:
            self._simulate_daily()
            
        if time_data["sim_triggers"]["global"]:
            self._simulate_global_economy()

        self.save_state()

    def _simulate_daily(self):
        """ Handles daily weather shifts and minor ecological events. """
        # Just a placeholder print for now to prove the clock works
        pass 

    def _simulate_global_economy(self):
        """ Runs every 30 days. Factions harvest, build, and grow. """
        print("\n[GLOBAL EVENT] Processing Faction Economies...")
        
        # 1. Map out who owns what
        faction_territories = {}
        for hex_cell in self.world_map.get("macro_map", []):
            owner = hex_cell.get("faction_owner", "")
            if owner:
                if owner not in faction_territories:
                    faction_territories[owner] = []
                faction_territories[owner].append(hex_cell)

        if not faction_territories:
            print("  -> No factions hold territory on the current map.")
            return

        # 2. Process each faction
        for faction_name, hexes in faction_territories.items():
            if faction_name not in self.state["factions"]:
                self.state["factions"][faction_name] = {"population": 1000, "treasury": 0, "wars_won": 0}
            
            f_state = self.state["factions"][faction_name]
            
            # Count Resources
            unique_materials = set()
            for hex_cell in hexes:
                unique_materials.update(hex_cell.get("local_resources", []))
                unique_materials.update(hex_cell.get("local_flora", []))
                unique_materials.update(hex_cell.get("local_fauna", []))
            
            material_count = len(unique_materials)
            # Count cities - depending on how cities are flagged in your map. Let's assume a bool 'is_city'
            total_cities = len([h for h in hexes if h.get("is_city", False)])
            
            # If no cities found initially, maybe give them one for free as their capital if they own territory
            if total_cities == 0 and len(hexes) > 0:
                total_cities = 1
                hexes[0]["is_city"] = True

            # Calculate Power & Infrastructure Unlocks (The logic we built!)
            f_state["treasury"] += (material_count * 10) + (total_cities * 50)
            f_state["population"] += int(f_state["population"] * 0.05) # 5% growth
            
            infrastructure = "CAMP"
            military = ["MILITIA"]
            logistics = "FOOT"
            
            if total_cities >= 2: logistics = "RIDING"
            if total_cities >= 4: logistics = "SAILING"

            if material_count >= 1 and f_state["population"] > 1000:
                infrastructure = "TOWN (Watchtowers)"
                military.extend(["ARCHERS"])
            if material_count >= 2 and f_state["population"] > 5000:
                infrastructure = "CITY (Walls)"
                military.extend(["SPEARMEN"])
                
            print(f" -> {faction_name} report:")
            print(f"    Territory: {len(hexes)} hexes | Cities: {total_cities}")
            
            if material_count > 0:
                print(f"    Economy: +{material_count} Unique Materials mined ({', '.join(unique_materials)}). Treasury now {f_state['treasury']}G")
            else:
                print(f"    Economy: No Unique Materials. Treasury now {f_state['treasury']}G")

            print(f"    Infrastructure Level: {infrastructure}")
            print(f"    Military Roster: {', '.join(military)}")
            print(f"    Logistics: {logistics}\n")

            # Log to Chronicle
            self.log_event(
                self.state["current_tick"],
                "ECONOMY",
                f"{faction_name} expanded their infrastructure to {infrastructure} and improved logistics to {logistics}.",
                location=hexes[0].get("id") if hexes else None
            )

if __name__ == "__main__":
    engine = ChronosEngine()
    # Simulate 30 days passing so we trigger the Global Economy event immediately
    engine.run_tick(days_to_advance=30)
