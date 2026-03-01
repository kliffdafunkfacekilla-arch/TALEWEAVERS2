#ifndef ECONOMY_ENGINE_H
#define ECONOMY_ENGINE_H

#include "../core/Types.h"
#include <string>
#include <vector>


class EconomyEngine {
public:
  /**
   * Updates the economic state of all cells.
   * Settlements produce goods based on local resources.
   */
  static void UpdateEconomy(std::vector<VoronoiCell> &cells);

  /**
   * Resolves trade between adjacent settlements or across the road network.
   */
  static void ResolveTrade(std::vector<VoronoiCell> &cells);

private:
  static void Produce(VoronoiCell &cell);
  static float GetBaseValue(const std::string &resource);
};

#endif
