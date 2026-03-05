#include "../../deps/nlohmann/json.hpp"
#include "../core/Types.h"
#include <fstream>
#include <iostream>
#include <map>
#include <vector>

using json = nlohmann::json;

/**
 * @brief Writes the final Master_World.json using nlohmann/json.
 *
 * Strictly follows the schema provided in the blueprint.
 */
class MasterExporter {
public:
  static void ExportWorld(const std::string &filename,
                          const std::string &worldName,
                          const std::vector<VoronoiCell> &cells,
                          const std::vector<Faction> &factions) {

    json j;

    // Metadata
    j["metadata"] = {{"world_name", worldName},
                     {"map_type", "VORONOI"},
                     {"cell_count", cells.size()}};

    // Time Rules (Sample data for scaffold)
    j["time_rules"] = {
        {"era", "Age of Awakening"},
        {"current_year", 1024},
        {"months", json::array({{{"name", "Frostfall"}, {"days", 30}}})},
        {"moons", json::array({{{"name", "Luna"},
                                {"cycle_days", 28.5},
                                {"force_even", false}}})},
        {"seasons",
         json::array({{{"name", "Deep Winter"}, {"temp_mod", -20.0}}})}};

    // Factions
    json jFactions = json::object();
    for (const auto &faction : factions) {
      json bldPrefs = json::array();
      for (const auto &b : faction.culture.building_preferences)
        bldPrefs.push_back(b);

      json prefBiomes = json::array();
      for (const auto &b : faction.preferred_biomes)
        prefBiomes.push_back(b);

      jFactions[faction.name] = {
          {"aggression", faction.aggression},
          {"expansion_rate", faction.expansion_rate},
          {"behaviors",
           {{"fight", faction.culture.will_fight},
            {"farm", faction.culture.will_farm},
            {"mine", faction.culture.will_mine},
            {"hunt", faction.culture.will_hunt},
            {"trade", faction.culture.will_trade},
            {"base_trade_value", faction.culture.base_trade_value}}},
          {"building_preferences", bldPrefs},
          {"loved_resources", faction.loved_resources},
          {"hated_resources", faction.hated_resources},
          {"required_resources", faction.required_resources},
          {"preferred_biomes", prefBiomes}};
    }
    j["factions"] = jFactions;

    // Macro Map
    json jCells = json::array();
    for (const auto &cell : cells) {
      json cell_json;
      cell_json["id"] = cell.id;
      cell_json["x"] = cell.x;
      cell_json["y"] = cell.y;
      cell_json["elevation"] = cell.elevation;
      cell_json["temperature"] = cell.temperature;
      cell_json["moisture"] = cell.moisture;
      cell_json["biome"] = cell.biome_tag;
      cell_json["biome_tag"] = cell.biome_tag;
      cell_json["faction_owner"] = cell.faction_owner;
      cell_json["has_river"] = cell.has_river;
      cell_json["settlement"] = cell.settlement_name;
      cell_json["settlement_tier"] = cell.settlement_tier;
      cell_json["dominant_religion"] = cell.dominant_religion;
      cell_json["constructed_buildings"] = cell.constructed_buildings;
      cell_json["available_resources"] = cell.available_resources;
      cell_json["local_resources"] = cell.local_resources;
      cell_json["local_fauna"] = cell.local_fauna;
      cell_json["threat_level"] = cell.threat_level;
      cell_json["market_state"] = cell.market_state;
      cell_json["production_rate"] = cell.production_rate;
      cell_json["road_next_id"] = cell.road_next_id;
      jCells.push_back(cell_json);
    }
    j["macro_map"] = jCells;

    // Road Network
    j["road_network"] = json::array();

    // Write to file
    std::ofstream file(filename);
    if (file.is_open()) {
      file << j.dump(4);
      std::cout << "Successfully exported world data to " << filename
                << std::endl;
    } else {
      std::cerr << "Failed to open " << filename << " for writing."
                << std::endl;
    }
  }
};
