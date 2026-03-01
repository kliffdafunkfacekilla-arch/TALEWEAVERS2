#include "VisibilityEngine.h"
#include <algorithm>
#include <cmath>

void VisibilityEngine::ComputeLOS(std::vector<VoronoiCell> &grid,
                                  int origin_idx, float view_range) {
  if (origin_idx < 0 || origin_idx >= (int)grid.size())
    return;

  const VoronoiCell &origin = grid[origin_idx];
  int grid_size = 96; // Standard Tier 4 grid size

  // Reset visibility for the current frame
  for (auto &node : grid) {
    node.is_visible = false;
  }

  // Origin is always visible and explored
  grid[origin_idx].is_visible = true;
  grid[origin_idx].is_explored = true;

  // Simple raycasting to every node in range
  for (int y = 0; y < grid_size; ++y) {
    for (int x = 0; x < grid_size; ++x) {
      int target_idx = y * grid_size + x;
      VoronoiCell &target = grid[target_idx];

      float dx = target.x - origin.x;
      float dy = target.y - origin.y;
      float dist = std::sqrt(dx * dx + dy * dy);

      if (dist > view_range)
        continue;
      if (target_idx == origin_idx)
        continue;

      // Raycast check
      bool obstructed = false;
      int steps = static_cast<int>(dist);
      if (steps < 1)
        steps = 1;

      for (int s = 1; s <= steps; ++s) {
        float t = (float)s / (float)steps;
        float cur_x = origin.x + dx * t;
        float cur_y = origin.y + dy * t;

        int ix = std::max(0, std::min(grid_size - 1, static_cast<int>(cur_x)));
        int iy = std::max(0, std::min(grid_size - 1, static_cast<int>(cur_y)));
        int check_idx = iy * grid_size + ix;

        // If we hit a high obstacle before reaching the target
        if (check_idx != target_idx) {
          const VoronoiCell &blocker = grid[check_idx];

          // LOS Rule: Trees and High Elevation block sight
          // If blocker in between is significantly higher than both origin and
          // target
          float origin_h = origin.elevation;
          float target_h = target.elevation;
          float blocker_h = blocker.elevation;

          // Forest check
          bool is_forest =
              (blocker.biome_tag == "FOREST" || blocker.biome_tag == "JUNGLE");

          if (is_forest && blocker_h > origin_h) {
            obstructed = true;
            break;
          }

          if (blocker_h > origin_h + 0.15f && blocker_h > target_h) {
            obstructed = true;
            break;
          }
        }
      }

      if (!obstructed) {
        target.is_visible = true;
        target.is_explored = true;
      }
    }
  }
}
