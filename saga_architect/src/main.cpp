#include "../deps/nlohmann/json.hpp"
#include "core/Types.h"
#include "io/Exporter.cpp"
#include "map/VoronoiGen.cpp"
#include "simulation/AutoPopulate.cpp"
#include "simulation/EconomyEngine.cpp"
#include "simulation/EntityEngine.cpp"
#include "simulation/VisibilityEngine.cpp"
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using json = nlohmann::json;

int main(int argc, char *argv[]) {
  std::cout << "==========================================\n";
  std::cout << "  T.A.L.E.W.E.A.V.E.R. World Architect    \n";
  std::cout << "==========================================\n";

  // 1. INGEST CUSTOMIZATION FILE
  std::ifstream configFile("architect_config.json");
  if (!configFile.is_open()) {
    std::cerr << "[ERROR] Could not find architect_config.json! Make sure it "
                 "is in the same directory as the executable.\n";
    return 1;
  }

  json config;
  configFile >> config;
  std::cout << "[INFO] Successfully loaded Lore & Customization parameters.\n";

  // 2. PARSE BIOMES
  std::vector<BiomeDef> biomeRules;
  for (const auto &b : config["biomes"]) {
    BiomeDef def;
    def.name = b["name"];
    def.temp_range = {b["min_temp"], b["max_temp"]};
    def.rain_range = {b["min_rain"], b["max_rain"]};
    biomeRules.push_back(def);
  }

  // 3. PARSE FACTIONS
  std::vector<Faction> factions;
  for (const auto &f : config["factions"]) {
    Faction fac;
    fac.name = f["name"];
    fac.aggression = f["aggression"];
    fac.culture.name = f["name"];
    fac.culture.will_fight = f.value("will_fight", false);
    fac.culture.will_farm = f.value("will_farm", false);
    fac.culture.will_mine = f.value("will_mine", false);
    fac.culture.will_hunt = f.value("will_hunt", false);
    fac.culture.will_trade = f.value("will_trade", false);
    fac.culture.base_trade_value = f.value("base_trade_value", 1.0f);
    for (const auto &bld : f.value("building_preferences", json::array())) {
      fac.culture.building_preferences.push_back(bld);
    }
    for (const auto &res : f.value("loved_resources", json::array())) {
      fac.loved_resources.push_back(res);
    }
    for (const auto &res : f.value("hated_resources", json::array())) {
      fac.hated_resources.push_back(res);
    }
    for (const auto &res : f.value("required_resources", json::array())) {
      fac.required_resources.push_back(res);
    }
    for (const auto &bio : f.value("preferred_biomes", json::array())) {
      fac.preferred_biomes.push_back(bio);
    }
    fac.expansion_rate = f.value("expansion_rate", 0.5f);
    factions.push_back(fac);
  }

  // 4. PARSE CLIMATE & WORLD SETTINGS
  int num_hexes = config["world_settings"].value("num_hexes", 2000);
  int world_width = config["world_settings"].value("width", 1000);
  int world_height = config["world_settings"].value("height", 1000);
  int tectonic_plates = config["world_settings"].value("tectonic_plates", 12);
  std::string heightmap_file =
      config["world_settings"].value("heightmap_image", "");

  ClimateRules climate;
  climate.north_pole_temp = {config["climate"]["north_pole"][0],
                             config["climate"]["north_pole"][1]};
  climate.equator_temp = {config["climate"]["equator"][0],
                          config["climate"]["equator"][1]};
  climate.south_pole_temp = {config["climate"]["south_pole"][0],
                             config["climate"]["south_pole"][1]};
  climate.rainfall_multiplier =
      config["climate"].value("rainfall_multiplier", 1.0f);
  for (const auto &band : config["climate"]["wind_bands"]) {
    climate.wind_bands.push_back(band);
  }

  // 4b. PARSE HEIGHTMAP STEPS
  std::vector<HeightmapStep> heightmap_steps;
  if (config.contains("heightmap_steps")) {
    for (const auto &s : config["heightmap_steps"]) {
      HeightmapStep hstep;
      hstep.tool = s.value("tool", "Hill");
      hstep.count = s.value("count", 1);
      hstep.height = s.value("height", 0.5f);

      if (s.contains("range_x") && s["range_x"].size() == 2) {
        hstep.range_x = {s["range_x"][0], s["range_x"][1]};
      } else {
        hstep.range_x = {0.0f, 1.0f};
      }
      if (s.contains("range_y") && s["range_y"].size() == 2) {
        hstep.range_y = {s["range_y"][0], s["range_y"][1]};
      } else {
        hstep.range_y = {0.0f, 1.0f};
      }
      heightmap_steps.push_back(hstep);
    }
  }

  // 5. PARSE FLORA & FAUNA
  std::vector<Lifeform> ecosystem;
  if (config.contains("flora_fauna")) {
    for (const auto &lf : config["flora_fauna"]) {
      Lifeform l;
      l.name = lf["name"];
      l.type = lf["type"];
      l.spawn_chance = lf["spawn_chance"];
      l.temp_range = {lf["min_temp"], lf["max_temp"]};

      // New biological parameters with defaults for backwards compatibility
      l.moisture_range = {lf.value("min_water", 0.0f),
                          lf.value("max_water", 1.0f)};
      l.is_aggressive = lf.value("is_aggressive", false);
      l.is_farmable = lf.value("is_farmable", false);
      l.is_tameable = lf.value("is_tameable", false);
      l.farm_yield_resource = lf.value("farm_yield_resource", "");
      l.farm_yield_amount = lf.value("farm_yield_amount", 0.0f);

      for (const auto &b : lf.value("allowed_biomes", json::array())) {
        l.allowed_biomes.push_back(b);
      }
      for (const auto &food : lf.value("diet", json::array())) {
        l.diet.push_back(food);
      }
      ecosystem.push_back(l);
    }
  }

  // 6. INITIALIZE ENGINES
  VoronoiGen physicalEngine;
  AutoPopulate civEngine;

  // New: Check for phase argument (if provided by Python API)
  std::string phase = "all";
  int target_hex = -1;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--phase" && i + 1 < argc)
      phase = argv[i + 1];
    if (arg == "--hex" && i + 1 < argc)
      target_hex = std::stoi(argv[i + 1]);
  }

  if (phase == "subgrid" && target_hex != -1) {
    std::cout << "[PHASE] Generating Local SubGrid for Hex #" << target_hex
              << "...\n";
    // We need the macro-map loaded first to provide context
    // (Simplified: for now, we assume 'all' was run and we are reloading or
    // generating fresh)
    physicalEngine.GenerateBaseMap(num_hexes, world_width, world_height);
    physicalEngine.SimulateClimate(climate);
    physicalEngine.SimulateHydrology();
    physicalEngine.AssignBiomes(biomeRules);
    civEngine.PopulateFactions(physicalEngine.cells, factions);
    civEngine.GenerateRoads(physicalEngine.cells);

    physicalEngine.GenerateSubGrid(target_hex);

    // 3. Compute Visibility (LOS & FOW) starting from the center of the subgrid
    // target_hex is the macro ID, we need to map it to a local index or just
    // use a default center. However, the local cells are ordered, so we usually
    // find the center-most node.
    int local_center_idx = physicalEngine.local_cells_cache.size() / 2;
    VisibilityEngine::ComputeLOS(physicalEngine.local_cells_cache,
                                 local_center_idx, 10.0f);

    // --- DYNAMIC ENTITY SPAWNING (Phase 34) ---
    // Fetch threat level from the parent hex
    int threat = 1;
    if (target_hex >= 0 && target_hex < (int)physicalEngine.cells.size()) {
      threat = physicalEngine.cells[target_hex].threat_level;
    }
    EntityEngine::PopulateEncounters(physicalEngine.local_cells_cache, threat);

    // 4. Update Detection (Stealth & Proximity)
    EntityEngine::UpdateDetection(physicalEngine.local_cells_cache,
                                  local_center_idx);

    // 5. Export to JSON
    physicalEngine.ExportSubGrid("Saga_Local_SubGrid.json");
    return 0;
  }

  std::cout << "\n[PHASE 1] Building Physical Planet (" << num_hexes
            << " hexes)...\n";
  physicalEngine.GenerateBaseMap(num_hexes, world_width, world_height);

  if (!heightmap_file.empty()) {
    physicalEngine.ImportHeightmap(heightmap_file);
  } else if (!heightmap_steps.empty()) {
    std::cout << "  Using procedural heightmap brushes ("
              << heightmap_steps.size() << " steps)...\n";
    physicalEngine.ApplyHeightmapSteps(heightmap_steps);
  } else {
    std::cout << "  Using tectonic simulation (" << tectonic_plates
              << " plates)...\n";
    physicalEngine.SimulateTectonics(tectonic_plates);
  }

  physicalEngine.SimulateClimate(climate);
  physicalEngine.SimulateHydrology();
  physicalEngine.AssignBiomes(biomeRules);

  std::cout << "\n[PHASE 2] Simulating Civilization & Ecosystem...\n";
  civEngine.PopulateFactions(physicalEngine.cells, factions);
  civEngine.GenerateRoads(physicalEngine.cells);

  // Drop the animals and plants into the world!
  civEngine.PopulateEcosystem(physicalEngine.cells, ecosystem);

  // [PHASE 4] Ecosystem & Resources
  civEngine.PopulateResourcesAndWildlife(physicalEngine.cells, biomeRules);

  // [PHASE 5] Economy & Trade
  std::cout << "[ECONOMY] Simulating market start...\n";
  EconomyEngine::UpdateEconomy(physicalEngine.cells);
  EconomyEngine::ResolveTrade(physicalEngine.cells);

  // EXPORT FINAL WORLD
  std::cout << "\n[EXPORT] Saving Planet to "
               "saga_vtt_client/public/data/world_data.json...\n";
  std::string outputPath = "Saga_Master_World.json";
  MasterExporter::ExportWorld(outputPath, "Aethelgard", physicalEngine.cells,
                              factions);

  std::cout << "\nSUCCESS: World generation complete. Saved to " << outputPath
            << "\n";
  std::cout << "  Hexes: " << num_hexes << "\n";
  std::cout << "  Factions: " << factions.size() << "\n";
  std::cout << "  Biomes: " << biomeRules.size() << "\n";
  std::cout << "  Cities: " << civEngine.city_nodes.size() << "\n";
  std::cout << "  Lifeforms Defined: " << ecosystem.size() << "\n";
  std::cout << "  Wind Bands: " << climate.wind_bands.size() << "\n";
  std::cout << "  Rainfall: x" << climate.rainfall_multiplier << "\n";
  if (!heightmap_file.empty()) {
    std::cout << "  Elevation: Heightmap (" << heightmap_file << ")\n";
  } else {
    std::cout << "  Elevation: Tectonic Simulation (" << tectonic_plates
              << " plates)\n";
  }
  return 0;
}
