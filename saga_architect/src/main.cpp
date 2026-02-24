#include "core/Types.h"
#include "io/Exporter.cpp"
#include <iostream>


int main() {
  std::cout << "SAGA World Architect Scaffold Initiated." << std::endl;

  // Sample data for verification
  std::vector<VoronoiCell> sampleCells;
  VoronoiCell cell0;
  cell0.id = 0;
  cell0.x = 45.2f;
  cell0.y = 12.8f;
  cell0.elevation = 0.8f;
  cell0.biome_tag = "TEMPERATE_DECIDUOUS";
  cell0.faction_owner = "Northern_Horde";
  cell0.has_river = true;
  cell0.settlement_name = "Iron_Spire_Keep";
  cell0.available_resources = {{"Iron", "infinite"}, {"Wood", "450"}};
  sampleCells.push_back(cell0);

  std::vector<Faction> sampleFactions;
  Faction horde;
  horde.name = "Northern_Horde";
  horde.aggression = 0.9f;
  horde.culture.will_fight = true;
  horde.culture.will_farm = false;
  horde.culture.will_mine = false;
  horde.culture.will_hunt = true;
  horde.culture.will_trade = true;
  horde.loved_resources = {"Iron"};
  horde.hated_resources = {"Magic_Dust"};
  sampleFactions.push_back(horde);

  // Trigger export
  MasterExporter::ExportWorld("Saga_Master_World.json", "Aethelgard",
                              sampleCells, sampleFactions);

  return 0;
}
