#include "EntityEngine.h"
#include <algorithm>
#include <cmath>

void EntityEngine::UpdateDetection(std::vector<VoronoiCell> &grid,
                                   int player_idx) {
  if (player_idx < 0 || player_idx >= (int)grid.size())
    return;

  for (int i = 0; i < (int)grid.size(); ++i) {
    if (grid[i].has_entity) {
      float effective_radius = CalculateEffectiveRadius(grid, i, player_idx);

      float dx = grid[i].x - grid[player_idx].x;
      float dy = grid[i].y - grid[player_idx].y;
      float dist = std::sqrt(dx * dx + dy * dy);

      if (dist <= effective_radius) {
        grid[i].is_alerted = true;
      } else {
        grid[i].is_alerted = false;
      }
    }
  }
}

float EntityEngine::CalculateEffectiveRadius(
    const std::vector<VoronoiCell> &grid, int entity_idx, int player_idx) {
  const VoronoiCell &entity = grid[entity_idx];
  const VoronoiCell &player = grid[player_idx];

  float base_radius = entity.detection_radius;
  float modifier = 1.0f;

  // --- STEALTH MODIFIERS ---

  // 1. Terrain Cover: Forests and Jungles reduce detection
  if (player.biome_tag == "FOREST" || player.biome_tag == "JUNGLE") {
    modifier *= 0.6f; // 40% reduction
  }

  // 2. Elevation: If player is higher than entity, they are harder to spot
  // (silhouette issues) or if entity is higher, they see better.
  if (player.elevation > entity.elevation + 0.1f) {
    modifier *= 0.8f; // 20% reduction
  } else if (entity.elevation > player.elevation + 0.1f) {
    modifier *= 1.3f; // 30% increase (high ground advantage)
  }

  // 3. Movement/Light (Placeholder for future: if player is "noisy")

  return std::max(1.0f, base_radius * modifier);
}

void EntityEngine::PopulateEncounters(std::vector<VoronoiCell> &grid,
                                      int threatLevel) {
  // Use a simple deterministic-style seed for now (re-seeding with threat)
  // In production, we should pass a specific seed for world consistency.
  for (int i = 0; i < (int)grid.size(); ++i) {
    auto &node = grid[i];

    // Skip spawning at center idx (where the player likely is)
    int center = grid.size() / 2;
    if (i == center)
      continue;

    // Probability of an encounter: (Threat / 50) + random jitter
    // Threat 12 = ~25% chance per chunk block? No, keep it rare.
    float spawnChance = (float)threatLevel / 100.0f;

    // We only spawn on walkable land
    if (node.biome_tag == "OCEAN")
      continue;

    // Pseudo-random roll (simulated)
    if ((rand() % 1000) / 1000.0f < spawnChance) {
      node.has_entity = true;
      node.detection_radius = 6.0f + (threatLevel / 2.0f);

      // Thematic Spawning
      if (node.biome_tag == "FOREST" || node.biome_tag == "JUNGLE") {
        node.entity_type = "HOSTILE_BANDIT";
      } else if (node.biome_tag == "MOUNTAIN") {
        node.entity_type = "HOSTILE_HARPY";
      } else if (node.biome_tag == "SWAMP" || node.biome_tag == "MOOR") {
        node.entity_type = "HOSTILE_GHOUL";
      } else {
        node.entity_type = "HOSTILE_WOLF";
      }
    }
  }
}
