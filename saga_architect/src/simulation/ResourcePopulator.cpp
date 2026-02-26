#pragma once

#include "../core/Types.h"
#include <iostream>
#include <random>
#include <vector>


class ResourcePopulator {
public:
  static void Populate(std::vector<VoronoiCell> &cells) {
    std::cout << "[AZGAAR PORT] Scattering the Architect's Palette (Resources, "
                 "Flora, Fauna)..."
              << std::endl;

    std::mt19937 gen(42); // Deterministic seed for now
    std::uniform_real_distribution<float> prob(0.0f, 1.0f);

    for (auto &cell : cells) {
      // Early exit for deep oceans
      if (cell.elevation <= 0.2f) {
        if (prob(gen) < 0.1f)
          cell.local_fauna.push_back("Leviathan");
        if (prob(gen) < 0.3f)
          cell.local_flora.push_back("Kelp_Forest");
        continue;
      }

      // 1. ELEVATION-BASED RESOURCES
      if (cell.elevation > 0.8f) { // High Mountains
        if (prob(gen) < 0.6f)
          cell.local_resources.push_back("Iron_Ore");
        if (prob(gen) < 0.2f)
          cell.local_resources.push_back("Aetherium_Vein");
        cell.threat_level = 4;
      } else if (cell.elevation > 0.6f) { // Hills
        if (prob(gen) < 0.4f)
          cell.local_resources.push_back("Stone");
        if (prob(gen) < 0.3f)
          cell.local_resources.push_back("Iron_Ore");
        cell.threat_level = 3;
      } else {                 // Flatlands
        cell.threat_level = 2; // Base threat
      }

      // 2. BIOME-BASED FLORA/FAUNA
      if (cell.biome_tag == "MUSHROOM_SWAMP") {
        if (prob(gen) < 0.8f)
          cell.local_flora.push_back("D-Dust_Spores");
        if (prob(gen) < 0.5f)
          cell.local_fauna.push_back("Bog_Stalker");
        cell.threat_level += 2; // Dangerous biome
      } else if (cell.biome_tag == "DEEP_TUNDRA") {
        if (prob(gen) < 0.4f)
          cell.local_fauna.push_back("Frost_Troll");
        if (prob(gen) < 0.2f)
          cell.local_resources.push_back("Ancient_Bones");
        cell.threat_level += 1;
      } else if (cell.biome_tag == "SCORCHED_DESERT") {
        if (prob(gen) < 0.5f)
          cell.local_flora.push_back("Sand_Cactus");
        if (prob(gen) < 0.3f)
          cell.local_fauna.push_back("Dune_Wraith");
        cell.threat_level += 1;
      } else if (cell.biome_tag == "LUSH_JUNGLE") {
        if (prob(gen) < 0.9f)
          cell.local_resources.push_back("Wood");
        if (prob(gen) < 0.6f)
          cell.local_flora.push_back("Healing_Herbs");
        if (prob(gen) < 0.5f)
          cell.local_fauna.push_back("Panther");
      }

      // Cap threat level at 5
      if (cell.threat_level > 5)
        cell.threat_level = 5;

      // If it's a city, threat level is lowered
      if (cell.is_city)
        cell.threat_level = 1;
    }
    std::cout << "[AZGAAR PORT] Palette Scattering Complete." << std::endl;
  }
};
