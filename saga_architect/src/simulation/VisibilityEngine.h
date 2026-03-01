#ifndef VISIBILITY_ENGINE_H
#define VISIBILITY_ENGINE_H

#include "../core/Types.h"
#include <vector>

class VisibilityEngine {
public:
  /**
   * Calculates Line of Sight (LOS) on a 96x96 grid from a starting node.
   * Updates 'is_visible' and 'is_explored' for nodes within range.
   * @param grid The 96x96 local nodes.
   * @param origin_idx The index of the player/origin node.
   * @param view_range The max distance in nodes.
   */
  static void ComputeLOS(std::vector<VoronoiCell> &grid, int origin_idx,
                         float view_range);

private:
  static bool IsObstructed(const VoronoiCell &origin,
                           const VoronoiCell &target);
};

#endif
