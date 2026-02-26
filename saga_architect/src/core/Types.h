#pragma once
#include <map>
#include <string>
#include <utility>
#include <vector>

// 1. TIME & CALENDAR
struct Moon {
  std::string name;
  float cycle_days;
  bool
      force_full_yearly_cycle; // If true, cycle adjusts to fit evenly in a year
};

struct Season {
  std::string name;
  int duration_days;
  float temp_modifier;
  float moisture_modifier;
};

// 2. BIOMES & RESOURCES
struct Resource {
  std::string name;
  float scarcity; // 0.0 (Rare) to 1.0 (Abundant)
  bool is_infinite;
};

struct BiomeDef {
  std::string name;
  std::pair<float, float> temp_range;
  std::pair<float, float> rain_range;
  std::vector<Resource> resources;
};

// 2b. CLIMATE RULES (Atmospheric Physics)
struct ClimateRules {
  std::pair<float, float> north_pole_temp; // {min, max}
  std::pair<float, float> equator_temp;    // {min, max}
  std::pair<float, float> south_pole_temp; // {min, max}
  float rainfall_multiplier;               // 0.0 (None) to 2.0 (Double Earth)
  std::vector<std::string> wind_bands; // 7 strings: N, NE, E, SE, S, SW, W, NW
};

// 3. FLORA & FAUNA (Ecosystem Entities)
struct Lifeform {
  std::string name;
  std::string type;                        // "FLORA" or "FAUNA"
  std::vector<std::string> allowed_biomes; // e.g., ["DEEP_TUNDRA", "ANY"]
  std::pair<float, float> temp_range; // Survives between these temps (+C, -C)
  std::pair<float, float>
      moisture_range; // Survives between these moisture levels (0.0=Bone
                      // Dry, 1.0=Underwater)
  std::vector<std::string>
      diet;           // e.g., ["Water", "Sunlight"] or ["Deer", "Rabbits"]
  float spawn_chance; // 0.01 (Rare) to 1.0 (Everywhere)
  bool is_aggressive;
  bool is_farmable;
  bool is_tameable;
  std::string farm_yield_resource; // What does farming this yield? (e.g.,
                                   // "Meat", "Wood")
  float farm_yield_amount;         // How much does it base-yield
};

// 4. CULTURE & FACTIONS
struct Culture {
  std::string name;
  bool will_fight;
  bool will_farm;
  bool will_mine;
  bool will_hunt;
  bool will_trade;
  float base_trade_value; // Economy multiplier
  std::vector<std::string>
      building_preferences; // e.g., ["Wood_Huts", "Stone_Keeps"]
};

struct Faction {
  std::string name;
  Culture culture;
  float aggression;
  float expansion_rate; // 0.0 to 1.0 (determines how fast borders grow)
  std::vector<std::string> required_resources; // Needed to build settlements
  std::vector<std::string> loved_resources;
  std::vector<std::string> hated_resources;
  std::vector<std::string> preferred_biomes; // Prioritized when settling
};

// 5. THE MAP NODE (Voronoi Cell)
struct VoronoiCell {
  int id;
  float x, y;                 // Center coordinate
  std::vector<int> neighbors; // IDs of touching cells
  int plate_id = -1;          // Tectonic plate identifier
  float elevation;            // 0.0 (Ocean) to 1.0 (Mountain Peak)
  float temperature;
  float moisture;
  float wind_dx; // Wind X direction (set by SimulateClimate)
  float wind_dy; // Wind Y direction (set by SimulateClimate)
  std::string biome_tag;
  std::string faction_owner;
  std::string settlement_name;
  bool has_river;
  std::map<std::string, std::string>
      available_resources; // e.g., {"Iron": "infinite", "Wood": "450"}

  // CULTURAL EXPANSION PROPERTIES
  float habitability = 0.0f;
  bool is_city = false;

  // THE FINER DETAILS (Architect's Palette)
  std::vector<std::string>
      local_resources; // e.g., ["Iron_Ore", "Ancient_Bones"]
  std::vector<std::string>
      local_fauna; // e.g., ["Frost_Troll", "Scavenger_Pack"]
  std::vector<std::string> local_flora; // e.g., ["D-Dust_Fungus"]
  int threat_level = 1;                 // 1 to 5
};
