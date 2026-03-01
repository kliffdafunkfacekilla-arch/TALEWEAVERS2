#ifndef ENTITY_ENGINE_H
#define ENTITY_ENGINE_H

#include "../core/Types.h"
#include <vector>

class EntityEngine {
public:
  /**
   * Updates detection states for all entities on the grid based on player
   * position.
   * @param grid The 96x96 local nodes.
   * @param player_idx The index of the player node.
   */
  static void UpdateDetection(std::vector<VoronoiCell> &grid, int player_idx);

  /**
   * Calculates the effective detection radius considering player stealth and
   * environment.
   * @param grid The 96x96 local nodes.
   * @param entity_idx The index of the entity node.
   * @param player_idx The index of the player node.
   * @return The modified detection radius.
   */
  static float CalculateEffectiveRadius(const std::vector<VoronoiCell> &grid,
                                        int entity_idx, int player_idx);

  /**
   * Spawns entities into the subgrid based on threat level and biome.
   * @param grid The local nodes to populate.
   * @param threatLevel 1-12 value from the parent macro-hex.
   */
  static void PopulateEncounters(std::vector<VoronoiCell> &grid,
                                 int threatLevel);
};

#endif
