#pragma once
#include <string>
#include <vector>
#include <utility>
#include <map>

// 1. TIME & CALENDAR
struct Moon {
    std::string name;
    float cycle_days;
    bool force_full_yearly_cycle; // If true, cycle adjusts to fit evenly in a year
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
    float scarcity;       // 0.0 (Rare) to 1.0 (Abundant)
    bool is_infinite;
};

struct BiomeDef {
    std::string name;
    std::pair<float, float> temp_range;
    std::pair<float, float> rain_range;
    std::vector<Resource> resources;
};

// 3. FLORA & FAUNA
struct Lifeform {
    std::string name;
    bool is_plant; // false = animal
    std::pair<float, float> temp_limits;
    std::pair<float, float> moisture_limits;
    std::string food_resource_needed;
    float growth_rate;
    float aggression;
    bool is_tamable;
    bool is_farmable;
    std::vector<std::string> resource_outputs; // e.g., ["Meat", "Pelt"]
};

// 4. CULTURE & FACTIONS
struct Culture {
    std::string name;
    bool will_fight;
    bool will_farm;
    bool will_mine;
    bool will_hunt;
    bool will_trade;
};

struct Faction {
    std::string name;
    Culture culture;
    float aggression;
    float expansion_rate;
    std::vector<std::string> required_resources; // Needed to build settlements
    std::vector<std::string> loved_resources;
    std::vector<std::string> hated_resources;
};

// 5. THE MAP NODE (Voronoi Cell)
struct VoronoiCell {
    int id;
    float x, y;                 // Center coordinate
    std::vector<int> neighbors; // IDs of touching cells
    float elevation;            // 0.0 (Ocean) to 1.0 (Mountain Peak)
    float temperature;
    float moisture;
    std::string biome_tag;
    std::string faction_owner;
    std::string settlement_name;
    bool has_river;
    std::map<std::string, std::string> available_resources; // e.g., {"Iron": "infinite", "Wood": "450"}
};
