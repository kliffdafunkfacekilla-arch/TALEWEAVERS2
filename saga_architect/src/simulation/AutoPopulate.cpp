#include "../core/Types.h"
#include <cmath>
#include <iostream>
#include <map>
#include <queue>
#include <random>
#include <vector>

class AutoPopulate {
public:
  std::vector<int> city_nodes;

  // Helper to evaluate how "good" a hex is for humanoids/cultures to live
  void CalculateHabitability(std::vector<VoronoiCell> &cells) {
    for (auto &cell : cells) {
      if (cell.elevation <= 0.2f) { // It's an ocean. You can't live underwater.
        cell.habitability = 0.0f;
        continue;
      }

      float hab = 0.0f;

      // 1. Temperature Preference (Ideal is around 15C to 25C)
      float temp_diff = std::abs(cell.temperature - 20.0f);
      if (temp_diff < 20.0f)
        hab += (20.0f - temp_diff) * 2.0f;

      // 2. Moisture/Rain Preference (Needs water, but not drowned)
      if (cell.moisture > 0.1f)
        hab += cell.moisture * 30.0f;

      // 3. Elevation Preference (Flatland is easier to farm than high peaks)
      if (cell.elevation < 0.6f)
        hab += (0.6f - cell.elevation) * 40.0f;

      // 4. Azgaar's Coastal/River bonus
      bool has_water = false;
      for (int n_idx : cell.neighbors) {
        if (cells[n_idx].elevation <= 0.2f || cells[n_idx].moisture > 0.8f) {
          has_water = true;
          break;
        }
      }
      if (has_water)
        hab += 40.0f;

      // Penalize extreme biomes heavily
      if (cell.biome_tag == "SCORCHED_DESERT" ||
          cell.biome_tag == "DEEP_TUNDRA") {
        hab *= 0.1f;
      }

      cell.habitability = std::max(0.0f, hab);
    }
  }

  // The Dijkstra Node for pathfinding
  struct ExpansionNode {
    int cell_idx;
    float cost;
    int faction_id;

    // Min-heap operator (lowest cost first)
    bool operator>(const ExpansionNode &other) const {
      return cost > other.cost;
    }
  };

  void PopulateFactions(std::vector<VoronoiCell> &cells,
                        const std::vector<Faction> &factions) {
    std::cout << "[AZGAAR PORT] Calculating Habitability & Organic Borders..."
              << std::endl;

    CalculateHabitability(cells);

    std::priority_queue<ExpansionNode, std::vector<ExpansionNode>,
                        std::greater<ExpansionNode>>
        frontier;

    // STEP 1: Find best starting locations (Capitals) for each faction
    for (size_t f = 0; f < factions.size(); ++f) {
      int best_cell = -1;
      float max_hab = -1.0f;

      for (size_t i = 0; i < cells.size(); ++i) {
        if (cells[i].faction_owner.empty() && cells[i].habitability > max_hab) {

          // Ensure capitals don't spawn right next to each other
          bool too_close = false;
          for (int n : cells[i].neighbors) {
            if (!cells[n].faction_owner.empty())
              too_close = true;
          }

          if (!too_close) {
            max_hab = cells[i].habitability;
            best_cell = i;
          }
        }
      }

      if (best_cell != -1) {
        cells[best_cell].faction_owner = factions[f].name;
        cells[best_cell].is_city = true; // Mark as Capital Burg
        cells[best_cell].settlement_name = factions[f].name + "_Capital";
        city_nodes.push_back(best_cell);

        // Add to expansion queue (Cost 0, because we start here)
        frontier.push({best_cell, 0.0f, (int)f});
      }
    }

    // STEP 2: Cost-based Territorial Expansion (Azgaar's Dijkstra Flood-Fill)
    while (!frontier.empty()) {
      ExpansionNode current = frontier.top();
      frontier.pop();

      int curr_idx = current.cell_idx;
      const Faction &curr_faction = factions[current.faction_id];

      for (int neighbor_idx : cells[curr_idx].neighbors) {
        VoronoiCell &neighbor = cells[neighbor_idx];

        // Stop at Oceans or already claimed land
        if (neighbor.elevation <= 0.2f || !neighbor.faction_owner.empty()) {
          continue;
        }

        // Calculate cost to physically enter this hex
        float enter_cost = 10.0f; // Base flatland cost

        // Mountains act as natural barriers (Cost skyrockets)
        if (neighbor.elevation > 0.6f)
          enter_cost += 100.0f;

        // Extreme biomes act as natural barriers
        if (neighbor.habitability < 10.0f)
          enter_cost += 50.0f;

        // DYNAMIC CULTURE BEHAVIOR: Does this faction natively prefer a
        // specific biome?
        if (curr_faction.name == "The_Rot_Coven" &&
            neighbor.biome_tag == "MUSHROOM_SWAMP") {
          enter_cost *= 0.2f; // Swamp costs them almost nothing to traverse
        } else if (curr_faction.name == "Iron_Empire" &&
                   neighbor.elevation > 0.5f) {
          enter_cost *= 0.5f; // They like hills/mountains for mining
        }

        float new_cost = current.cost + enter_cost;

        // Maximum Expansion Range: Multiplied by the Faction's Aggression
        // slider!
        float max_expansion = curr_faction.aggression * 800.0f;

        if (new_cost < max_expansion) {
          neighbor.faction_owner = curr_faction.name;
          frontier.push({neighbor_idx, new_cost, current.faction_id});
        }
      }
    }
    std::cout << "[AZGAAR PORT] Societal Expansion Complete." << std::endl;
  }

  // A* Pathfinding implementation for roads
  void GenerateRoads(std::vector<VoronoiCell> &cells) {
    std::cout << "Generating road network via A*..." << std::endl;
    if (city_nodes.size() < 2)
      return;

    for (size_t i = 0; i < city_nodes.size() - 1; ++i) {
      int start_id = city_nodes[i];
      int goal_id = city_nodes[i + 1];
      RunAStar(cells, start_id, goal_id);
    }
  }

  // Ecosystem Populator — tests biological survival conditions per hex
  void PopulateEcosystem(std::vector<VoronoiCell> &cells,
                         const std::vector<Lifeform> &lifeforms) {
    std::cout << "[INFO] Seeding Flora and Fauna...\n";
    if (lifeforms.empty())
      return;

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> chance(0.0f, 1.0f);

    int total_spawned = 0;

    for (auto &cell : cells) {
      // Oceans are ignored unless you add an "AQUATIC" flag later
      if (cell.elevation <= 0.05f)
        continue;

      for (const auto &lf : lifeforms) {
        // 1. Biological Temp Check
        if (cell.temperature < lf.temp_range.first ||
            cell.temperature > lf.temp_range.second) {
          continue; // Too hot or too cold!
        }

        // 2. Biological Moisture Check
        if (cell.moisture < lf.moisture_range.first ||
            cell.moisture > lf.moisture_range.second) {
          continue; // Too dry or too flooded!
        }

        // 3. Biome Check
        bool valid_biome = false;
        for (const auto &b : lf.allowed_biomes) {
          if (b == "ANY" || b == cell.biome_tag) {
            valid_biome = true;
            break;
          }
        }
        if (!valid_biome)
          continue;

        // 3. RNG Spawn Check (Did it successfully grow here?)
        if (chance(gen) <= lf.spawn_chance) {
          if (lf.type == "FLORA") {
            cell.local_flora.push_back(lf.name);
          } else {
            cell.local_fauna.push_back(lf.name);
          }
          if (lf.is_aggressive) {
            cell.threat_level += 1;
          }
          total_spawned++;
        }
      }
    }
    std::cout << "[INFO] Ecosystem stabilized. " << total_spawned
              << " lifeform populations spawned.\n";
  }

  void PopulateResourcesAndWildlife(std::vector<VoronoiCell> &grid,
                                    const std::vector<BiomeDef> &biomeRules) {
    std::cout << "[S.A.G.A. PORT] Seeding Minerals and Biome Resources..."
              << std::endl;

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);

    // Map Biome names to their definitions for fast lookup
    std::map<std::string, const BiomeDef *> biomeMap;
    for (const auto &b : biomeRules) {
      biomeMap[b.name] = &b;
    }

    for (auto &cell : grid) {
      if (cell.elevation <= 0.2f) {
        // Ocean Resources - Hardcoded fallback since oceans lack true biomes
        // currently
        if (dist(gen) < 0.3f)
          cell.local_resources.push_back("Salt");
        continue;
      }

      // --- 1. GEOLOGICAL MINERALS (Based on Tectonics) ---
      if (cell.elevation > 0.8f) { // High Mountains
        if (dist(gen) < 0.40f)
          cell.local_resources.push_back("Iron_Ore");
        if (dist(gen) < 0.20f)
          cell.local_resources.push_back("Obsidian");
      } else if (cell.elevation > 0.6f) { // Hills
        if (dist(gen) < 0.15f)
          cell.local_resources.push_back("Iron_Ore");
        if (dist(gen) < 0.30f)
          cell.local_resources.push_back("Coal");
      }

      // --- 2. DYNAMIC BIOME SPECIFIC LOOT ---
      if (biomeMap.count(cell.biome_tag)) {
        const BiomeDef *bDef = biomeMap[cell.biome_tag];
        for (const auto &res : bDef->resources) {
          // Scarcity acts as the spawn probability (0.0 to 1.0)
          if (dist(gen) <= res.scarcity) {
            cell.local_resources.push_back(res.name);
          }
        }
      }

      // General scavengers follow habitability (where things die)
      if (cell.habitability > 20.0f) {
        if (dist(gen) < 0.50f)
          cell.local_fauna.push_back("Wild_Game");
      }
    }

    std::cout << "[S.A.G.A. PORT] Resource generation complete." << std::endl;
  }

  // 6. Simulate Religion (Spreads organically based on habitability and
  // contact)
  void SimulateReligion(std::vector<VoronoiCell> &cells,
                        const std::vector<Religion> &religions,
                        const std::vector<Faction> &factions) {
    if (religions.empty())
      return;
    std::cout << "[AZGAAR PORT] Spreading Religions..." << std::endl;

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> rel_dist(0, religions.size() - 1);

    // Randomly assign a dominant religion to each capital city
    for (int city_idx : city_nodes) {
      cells[city_idx].dominant_religion = religions[rel_dist(gen)].name;
    }

    // Simple flood-fill diffusion for religion
    int spread_passes = 10;
    for (int p = 0; p < spread_passes; ++p) {
      std::vector<std::string> next_religion(cells.size(), "");
      for (size_t i = 0; i < cells.size(); ++i) {
        if (cells[i].dominant_religion.empty() &&
            !cells[i].faction_owner.empty()) {
          // Count neighbor religions
          std::map<std::string, int> rel_counts;
          for (int n : cells[i].neighbors) {
            if (!cells[n].dominant_religion.empty()) {
              rel_counts[cells[n].dominant_religion]++;
            }
          }
          if (!rel_counts.empty()) {
            std::string best_rel = "";
            int max_c = 0;
            for (auto const &[rel, count] : rel_counts) {
              if (count > max_c) {
                max_c = count;
                best_rel = rel;
              }
            }
            next_religion[i] = best_rel;
          }
        }
      }
      // Apply spreading
      for (size_t i = 0; i < cells.size(); ++i) {
        if (cells[i].dominant_religion.empty() && !next_religion[i].empty()) {
          cells[i].dominant_religion = next_religion[i];
        }
      }
    }
  }

  // 7. Develop Settlements (Upgrade Tiers and Construct Buildings)
  void DevelopSettlements(std::vector<VoronoiCell> &cells,
                          const std::vector<BuildingDef> &buildings,
                          const std::vector<Faction> &factions) {
    std::cout << "[AZGAAR PORT] Developing Settlements and Buildings..."
              << std::endl;

    // Create a fast lookup for factions
    std::map<std::string, const Faction *> fac_map;
    for (const auto &f : factions) {
      fac_map[f.name] = &f;
    }

    for (int i : city_nodes) {
      VoronoiCell &city = cells[i];
      city.settlement_tier = 4; // Capital starts at City tier 4

      const Faction *fac = fac_map[city.faction_owner];
      if (!fac)
        continue;

      // Build starting preferred buildings
      for (const std::string &pref : fac->culture.building_preferences) {
        // Ensure we only build things that exist in the BuildingDef and meet
        // the tier
        for (const auto &bdef : buildings) {
          if (bdef.name == pref && city.settlement_tier >= bdef.minimum_tier) {
            city.constructed_buildings.push_back(pref);
            break;
          }
        }
      }
    }

    // Also create minor settlements on high habitability nodes
    for (size_t i = 0; i < cells.size(); ++i) {
      VoronoiCell &cell = cells[i];
      if (!cell.faction_owner.empty() && cell.habitability > 50.0f &&
          !cell.is_city) {
        // 10% chance to form a minor settlement (Village/Town)
        if ((rand() % 100) < 10) {
          cell.settlement_name = cell.faction_owner + "_Outpost";
          cell.settlement_tier = (rand() % 2) + 1; // Tier 1 or 2

          // Maybe build a basic structure
          const Faction *fac = fac_map[cell.faction_owner];
          if (fac && !fac->culture.building_preferences.empty()) {
            std::string pref = fac->culture.building_preferences[0];
            for (const auto &bdef : buildings) {
              if (bdef.name == pref &&
                  cell.settlement_tier >= bdef.minimum_tier) {
                cell.constructed_buildings.push_back(pref);
                break;
              }
            }
          }
        }
      }
    }
  }

  // 8. Seed Points of Interest (Adventure Locations outside of Settlements)
  void SeedPointsOfInterest(std::vector<VoronoiCell> &cells,
                            const std::vector<BuildingDef> &buildings) {
    std::cout << "[AZGAAR PORT] Seeding Points of Interest (Lairs, Ruins, "
                 "Dungeons)..."
              << std::endl;

    std::vector<const BuildingDef *> adventure_buildings;
    for (const auto &b : buildings) {
      if (b.type == "Adventure") {
        adventure_buildings.push_back(&b);
      }
    }

    if (adventure_buildings.empty())
      return;

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> b_dist(0,
                                              adventure_buildings.size() - 1);
    std::uniform_int_distribution<int> chance_dist(1, 100);

    for (size_t i = 0; i < cells.size(); ++i) {
      VoronoiCell &cell = cells[i];

      // POIs only spawn on land and usually away from big cities
      if (cell.elevation <= 0.2f || cell.settlement_tier >= 3)
        continue;

      int spawn_chance = 0;

      // Higher threat = higher chance of POIs (Lairs, Dungeons)
      if (cell.threat_level > 50) {
        spawn_chance += 10;
      }
      // Extreme biomes have higher chance for Caves/Ruins (less civilized)
      if (cell.biome_tag == "SCORCHED_DESERT" ||
          cell.biome_tag == "DEEP_TUNDRA" || cell.biome_tag == "MOUNTAIN") {
        spawn_chance += 15;
      }
      // General wilderness baseline
      if (cell.faction_owner.empty() && cell.settlement_tier == 0) {
        spawn_chance += 5;
      }

      if (spawn_chance > 0 && chance_dist(gen) <= spawn_chance) {
        const BuildingDef *poi = adventure_buildings[b_dist(gen)];
        cell.constructed_buildings.push_back(poi->name);
      }
    }
  }

private:
  // Helper structure for A* Priority Queue
  struct AStarNode {
    int id;
    float f_score;
    bool operator>(const AStarNode &other) const {
      return f_score > other.f_score;
    }
  };

  void RunAStar(std::vector<VoronoiCell> &cells, int start, int goal) {
    std::priority_queue<AStarNode, std::vector<AStarNode>,
                        std::greater<AStarNode>>
        openSet;
    std::map<int, int> cameFrom;
    std::map<int, float> gScore;

    for (const auto &cell : cells)
      gScore[cell.id] = 999999.0f;

    gScore[start] = 0;
    openSet.push({start, Heuristic(cells[start], cells[goal])});

    while (!openSet.empty()) {
      int current = openSet.top().id;
      openSet.pop();

      if (current == goal) {
        // Backtrack to mark the road
        int temp = goal;
        while (temp != start) {
          int parent = cameFrom[temp];
          cells[parent].has_road = true;
          cells[parent].road_next_id = temp;
          temp = parent;
        }
        return;
      }

      for (int neighbor : cells[current].neighbors) {
        float el_diff =
            std::abs(cells[current].elevation - cells[neighbor].elevation);
        float step_cost = 1.0f + (el_diff * 10.0f);

        if (cells[neighbor].elevation > 0.8f)
          step_cost += 100.0f;

        float tentative_gScore = gScore[current] + step_cost;

        if (tentative_gScore < gScore[neighbor]) {
          cameFrom[neighbor] = current;
          gScore[neighbor] = tentative_gScore;
          float fScore =
              tentative_gScore + Heuristic(cells[neighbor], cells[goal]);
          openSet.push({neighbor, fScore});
        }
      }
    }
  }

  float Heuristic(const VoronoiCell &a, const VoronoiCell &b) {
    return std::sqrt(std::pow(a.x - b.x, 2) + std::pow(a.y - b.y, 2));
  }
};
