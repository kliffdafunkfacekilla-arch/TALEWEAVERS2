#include "core/Types.h"
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

#include "io/Exporter.cpp"
#include "map/VoronoiGen.cpp"
#include "simulation/AutoPopulate.cpp"
#include "simulation/ResourcePopulator.cpp"

using json = nlohmann::json;

int main() {
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

  std::cout << "\n[PHASE 1] Building Physical Planet (" << num_hexes
            << " hexes)...\n";
  physicalEngine.GenerateBaseMap(num_hexes);

  if (!heightmap_file.empty()) {
    physicalEngine.ImportHeightmap(heightmap_file);
  } else {
    std::cout << "  Using tectonic simulation (" << tectonic_plates
              << " plates)...\n";
    physicalEngine.SimulateTectonics(tectonic_plates);
  }

  physicalEngine.SimulateClimate(climate);
  physicalEngine.AssignBiomes(biomeRules);

  std::cout << "\n[PHASE 2] Simulating Civilization & Ecosystem...\n";
  civEngine.PopulateFactions(physicalEngine.cells, factions);
  civEngine.GenerateRoads(physicalEngine.cells);

  // Drop the animals and plants into the world!
  civEngine.PopulateEcosystem(physicalEngine.cells, ecosystem);

  // Scatter Architect Palette (Resources, specific Flora/Fauna rules)
  civEngine.PopulateResourcesAndWildlife(physicalEngine.cells);

  // 7. Export to JSON
  std::cout << "\n[PHASE 3] Packaging Data...\n";
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
