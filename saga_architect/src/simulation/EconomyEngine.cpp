#include "EconomyEngine.h"
#include <algorithm>
#include <iostream>

void EconomyEngine::UpdateEconomy(std::vector<VoronoiCell> &cells,
                                  const std::vector<BuildingDef> &buildings) {
  for (auto &cell : cells) {
    if (!cell.settlement_name.empty() || cell.is_city) {
      Produce(cell, buildings);
    }
  }
}

void EconomyEngine::Produce(VoronoiCell &cell,
                            const std::vector<BuildingDef> &buildings) {
  // Basic production logic: iterate through local resources and generate supply
  for (const auto &res : cell.local_resources) {
    // Simple increment for now, could be scaled by production_rate
    cell.market_state[res] += 1.0f + cell.production_rate;
  }

  // Settlements also "consume" basic needs (Demand)
  cell.market_state["Food"] -= 0.5f;
  cell.market_state["Water"] -= 0.5f;

  // Cities have higher demands
  if (cell.is_city) {
    cell.market_state["Luxury_Goods"] -= 0.1f;
    cell.market_state["Aetherium"] -= 0.05f;
  }

  // DEEP BUILDING LOGIC (Consume upkeep, yield production)
  for (const std::string &b_name : cell.constructed_buildings) {
    for (const auto &bdef : buildings) {
      if (bdef.name == b_name) {
        // Upkeep (Consumption)
        for (const auto &[req_res, amount] : bdef.upkeep) {
          cell.market_state[req_res] -= amount;
        }
        // Production (Yield)
        for (const auto &[prod_res, amount] : bdef.production) {
          cell.market_state[prod_res] += amount;
        }
        break;
      }
    }
  }
}

void EconomyEngine::ResolveTrade(std::vector<VoronoiCell> &cells) {
  // Trade flows from High Supply to High Demand
  for (size_t i = 0; i < cells.size(); ++i) {
    if (cells[i].settlement_name.empty() && !cells[i].is_city)
      continue;

    for (int neighbor_idx : cells[i].neighbors) {
      VoronoiCell &neighbor = cells[neighbor_idx];
      if (neighbor.settlement_name.empty() && !neighbor.is_city)
        continue;

      // Resolve each resource
      for (auto &[resource, supply] : cells[i].market_state) {
        float demand = neighbor.market_state[resource];

        // If I have high supply and you have high demand (negative supply)
        if (supply > 1.0f && demand < 0.0f) {
          float trade_amount = std::min(supply - 1.0f, -demand);
          cells[i].market_state[resource] -= trade_amount;
          neighbor.market_state[resource] += trade_amount;
        }
      }
    }
  }
}

float EconomyEngine::GetBaseValue(const std::string &resource) {
  if (resource == "Aetherium")
    return 100.0f;
  if (resource == "Iron_Ore")
    return 10.0f;
  if (resource == "Food")
    return 2.0f;
  return 1.0f;
}
