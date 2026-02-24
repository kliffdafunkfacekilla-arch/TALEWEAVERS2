#include "core/Types.h"
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>


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
      jFactions[faction.name] = {{"aggression", faction.aggression},
                                 {"behaviors",
                                  {{"fight", faction.culture.will_fight},
                                   {"farm", faction.culture.will_farm},
                                   {"mine", faction.culture.will_mine},
                                   {"hunt", faction.culture.will_hunt},
                                   {"trade", faction.culture.will_trade}}},
                                 {"loved_resources", faction.loved_resources},
                                 {"hated_resources", faction.hated_resources}};
    }
    j["factions"] = jFactions;

    // Macro Map
    json jCells = json::array();
    for (const auto &cell : cells) {
      jCells.push_back({{"cell_id", cell.id},
                        {"coord", {cell.x, cell.y}},
                        {"elevation", cell.elevation},
                        {"biome", cell.biome_tag},
                        {"faction_owner", cell.faction_owner},
                        {"has_river", cell.has_river},
                        {"settlement", cell.settlement_name},
                        {"available_resources", cell.available_resources}});
    }
    j["macro_map"] = jCells;

    // Road Network (Sample data for scaffold)
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
