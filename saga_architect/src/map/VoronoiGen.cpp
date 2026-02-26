#include "core/Types.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <map>
#include <queue>
#include <random>
#include <vector>

// Include stb_image for PNG reading
#define STB_IMAGE_IMPLEMENTATION
#include "../stb_image.h"

class VoronoiGen {
public:
  std::vector<VoronoiCell> cells;

  void GenerateBaseMap(int cellCount) {
    std::cout << "Generating " << cellCount << " Voronoi cells..." << std::endl;
    cells.resize(cellCount);

    for (int i = 0; i < cellCount; ++i) {
      cells[i].id = i;
      cells[i].x = static_cast<float>(rand() % 1000);
      cells[i].y = static_cast<float>(rand() % 1000);
      cells[i].elevation = 0.2f;
      cells[i].temperature = 20.0f;
      cells[i].moisture = 0.5f;
      cells[i].wind_dx = 0.0f;
      cells[i].wind_dy = 0.0f;
      cells[i].has_river = false;
    }
  }

  // Photo Importer — reads a grayscale PNG and maps pixel brightness to
  // elevation
  void ImportHeightmap(const std::string &filename) {
    std::cout << "[INFO] Importing Map Data from " << filename << "..."
              << std::endl;

    int width, height, channels;
    unsigned char *img =
        stbi_load(filename.c_str(), &width, &height, &channels, 1);

    if (img == NULL) {
      std::cerr << "[ERROR] Could not load " << filename
                << ". Falling back to Tectonic simulation.\n";
      SimulateTectonics(12);
      return;
    }

    for (auto &cell : cells) {
      int px = static_cast<int>((cell.x / 1000.0f) * width);
      int py = static_cast<int>((cell.y / 1000.0f) * height);
      px = std::max(0, std::min(px, width - 1));
      py = std::max(0, std::min(py, height - 1));
      unsigned char pixel_val = img[py * width + px];
      cell.elevation = pixel_val / 255.0f;
    }

    stbi_image_free(img);
    std::cout << "[INFO] Heightmap applied. Tectonics bypassed.\n";
  }

  // Helper for Heightmap Brushes
  int FindClosestCell(float x, float y) {
    if (cells.empty())
      return -1;
    int best = 0;
    float min_dist = 9999999.0f;
    for (size_t i = 0; i < cells.size(); i++) {
      float dx = cells[i].x - x;
      float dy = cells[i].y - y;
      float ds = dx * dx + dy * dy;
      if (ds < min_dist) {
        min_dist = ds;
        best = i;
      }
    }
    return best;
  }

  // --- AZGAAR FANTASY MAP GENERATOR: HEIGHTMAP SCULPTING BRUSHES ---
  void ApplyHeightmapSteps(const std::vector<HeightmapStep> &steps) {
    if (steps.empty())
      return;
    std::cout << "[AZGAAR PORT] Running " << steps.size()
              << " Procedural Heightmap Brushes...\n";
    for (const auto &step : steps) {
      if (step.tool == "Hill")
        AddHill(step);
      else if (step.tool == "Pit")
        AddPit(step);
      else if (step.tool == "Range")
        AddRange(step);
      else if (step.tool == "Smooth")
        Smooth(step);
    }
  }

  void AddHill(const HeightmapStep &step) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> rand_x(step.range_x.first * 1000.0f,
                                                 step.range_x.second * 1000.0f);
    std::uniform_real_distribution<float> rand_y(step.range_y.first * 1000.0f,
                                                 step.range_y.second * 1000.0f);
    std::uniform_real_distribution<float> fuzz(0.9f, 1.1f);

    float blobPower = 0.95f;

    for (int i = 0; i < step.count; i++) {
      int start_idx = FindClosestCell(rand_x(gen), rand_y(gen));
      if (start_idx == -1)
        continue;

      std::vector<float> change(cells.size(), 0.0f);
      // Using Azgaar's 1-100 scale math internally to match his decay curve
      change[start_idx] = step.height * 100.0f;

      std::queue<int> queue;
      queue.push(start_idx);

      while (!queue.empty()) {
        int q = queue.front();
        queue.pop();

        for (int n : cells[q].neighbors) {
          if (change[n] > 0.0f)
            continue;
          // Height decay like Azgaar
          change[n] = std::pow(change[q], blobPower) * fuzz(gen);

          if (change[n] > 1.0f)
            queue.push(n);
        }
      }

      for (size_t c = 0; c < cells.size(); c++) {
        cells[c].elevation =
            std::min(1.0f, cells[c].elevation + (change[c] / 100.0f));
      }
    }
  }

  void AddPit(const HeightmapStep &step) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> rand_x(step.range_x.first * 1000.0f,
                                                 step.range_x.second * 1000.0f);
    std::uniform_real_distribution<float> rand_y(step.range_y.first * 1000.0f,
                                                 step.range_y.second * 1000.0f);
    std::uniform_real_distribution<float> fuzz(0.9f, 1.1f);

    for (int i = 0; i < step.count; i++) {
      int start_idx = FindClosestCell(rand_x(gen), rand_y(gen));

      std::vector<bool> used(cells.size(), false);
      float h = step.height * 100.0f;

      std::queue<int> queue;
      queue.push(start_idx);

      while (!queue.empty()) {
        int q = queue.front();
        queue.pop();

        h = std::pow(h, 0.95f) * fuzz(gen);
        if (h < 1.0f)
          break;

        for (int c : cells[q].neighbors) {
          if (used[c])
            continue;
          used[c] = true;

          cells[c].elevation =
              std::max(0.05f, cells[c].elevation - ((h * fuzz(gen)) / 100.0f));
          queue.push(c);
        }
      }
    }
  }

  void AddRange(const HeightmapStep &step) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> rand_x(step.range_x.first * 1000.0f,
                                                 step.range_x.second * 1000.0f);
    std::uniform_real_distribution<float> rand_y(step.range_y.first * 1000.0f,
                                                 step.range_y.second * 1000.0f);
    std::uniform_real_distribution<float> fuzz(0.85f, 1.15f);

    for (int i = 0; i < step.count; i++) {
      int start_c = FindClosestCell(rand_x(gen), rand_y(gen));
      int end_c = FindClosestCell(rand_x(gen), rand_y(gen));

      // Generate Path (Ridge Line)
      std::vector<int> range_line;
      int cur = start_c;
      std::vector<bool> used(cells.size(), false);
      used[cur] = true;

      while (cur != end_c && cur != -1) {
        float min_diff = 9999999.0f;
        int next_c = -1;

        for (int n : cells[cur].neighbors) {
          if (used[n])
            continue;

          float dx = cells[end_c].x - cells[n].x;
          float dy = cells[end_c].y - cells[n].y;
          float dist_sq = dx * dx + dy * dy;

          if (fuzz(gen) > 1.0f)
            dist_sq *= 0.5f; // Azgaar Randomness
          if (dist_sq < min_diff) {
            min_diff = dist_sq;
            next_c = n;
          }
        }

        if (next_c == -1)
          break;
        range_line.push_back(next_c);
        used[next_c] = true;
        cur = next_c;
      }

      // Swell outwards
      std::queue<int> q;
      std::fill(used.begin(), used.end(), false);
      for (int r : range_line) {
        q.push(r);
        used[r] = true;
      }

      float h = step.height * 100.0f;
      float linePower = 0.81f; // Azgaar constant

      while (!q.empty()) {
        std::vector<int> frontier;
        while (!q.empty()) {
          frontier.push_back(q.front());
          q.pop();
        }

        for (int f : frontier) {
          cells[f].elevation =
              std::min(1.0f, cells[f].elevation + ((h * fuzz(gen)) / 100.0f));
        }

        h = std::pow(h, linePower) - 1.0f;
        if (h < 2.0f)
          break;

        for (int f : frontier) {
          for (int n : cells[f].neighbors) {
            if (!used[n]) {
              q.push(n);
              used[n] = true;
            }
          }
        }
      }
    }
  }

  void Smooth(const HeightmapStep &step) {
    for (int i = 0; i < step.count; i++) {
      std::vector<float> smoothed(cells.size(), 0.0f);
      for (size_t c = 0; c < cells.size(); c++) {
        float sum = cells[c].elevation;
        for (int n : cells[c].neighbors) {
          sum += cells[n].elevation;
        }
        smoothed[c] = sum / (cells[c].neighbors.size() + 1);
      }
      for (size_t c = 0; c < cells.size(); c++) {
        cells[c].elevation = smoothed[c];
      }
    }
  }

  // Math helper for plate collisions (The Dot Product)
  float CalculateCollisionImpact(float dx1, float dy1, float dx2, float dy2,
                                 float nx, float ny) {
    // Relative velocity of Plate 1 to Plate 2
    float vx = dx1 - dx2;
    float vy = dy1 - dy2;

    // Dot product against the boundary normal (nx, ny)
    // Positive means they are crashing into each other. Negative means pulling
    // apart.
    return (vx * nx + vy * ny);
  }

  void SimulateTectonics(int num_plates) {
    std::cout << "[AZGAAR PORT] Initiating Tectonic Blob Expansion ("
              << num_plates << " plates)..." << std::endl;

    if (cells.empty())
      return;

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> cell_dist(0, cells.size() - 1);
    std::uniform_real_distribution<> vector_dist(-1.0f, 1.0f);

    struct Plate {
      int id;
      float dx, dy; // Movement vectors
      float base_elevation;
    };

    std::vector<Plate> plates;
    std::queue<int> frontier; // For BFS expansion

    // Reset plate_ids just in case
    for (auto &cell : cells) {
      cell.plate_id = -1;
    }

    // STEP 1: Seed the Tectonic Plates (Azgaar's Blob Centers)
    for (int i = 0; i < num_plates; i++) {
      int seed_idx = cell_dist(gen);
      // Find an empty cell
      while (cells[seed_idx].plate_id != -1) {
        seed_idx = cell_dist(gen);
      }

      Plate p;
      p.id = i;
      // Random vector direction
      p.dx = vector_dist(gen);
      p.dy = vector_dist(gen);

      // Normalize the vector
      float mag = std::sqrt(p.dx * p.dx + p.dy * p.dy);
      if (mag > 0.0f) {
        p.dx /= mag;
        p.dy /= mag;
      }

      // Is this an oceanic plate or a continental plate?
      // Use an organic distance formula from the center of the map to encourage
      // a central Pangaea archipelago rather than a blocky stripe
      float map_center_x = 500.0f; // Approx center for 1000 bounds
      float map_center_y = 500.0f; // Approx center for 1000 bounds
      float dist_x = std::abs(cells[seed_idx].x - map_center_x) / map_center_x;
      float dist_y = std::abs(cells[seed_idx].y - map_center_y) / map_center_y;
      float dist_from_center = std::sqrt(dist_x * dist_x + dist_y * dist_y);

      // If we are near the edge of the world, 90% chance to be Ocean
      // If we are near the center, 70% chance to be Land
      float land_chance = 0.7f - (dist_from_center * 0.6f);
      p.base_elevation =
          (vector_dist(gen) < (land_chance * 2.0f - 1.0f)) ? 0.5f : 0.05f;

      plates.push_back(p);

      cells[seed_idx].plate_id = i;
      cells[seed_idx].elevation = p.base_elevation;
      frontier.push(seed_idx);
    }

    // STEP 2: Grow the plates outward (Azgaar's Breadth-First Expansion)
    while (!frontier.empty()) {
      int current_idx = frontier.front();
      frontier.pop();

      int current_plate = cells[current_idx].plate_id;

      // Iterate through all physical neighbors of this hex
      for (int neighbor_idx : cells[current_idx].neighbors) {
        if (cells[neighbor_idx].plate_id == -1) {
          // Claim the neighbor
          cells[neighbor_idx].plate_id = current_plate;

          // Add minor organic jitter to elevation (Azgaar's noise pass)
          float jitter = vector_dist(gen) * 0.05f;
          cells[neighbor_idx].elevation =
              plates[current_plate].base_elevation + jitter;

          frontier.push(neighbor_idx);
        }
      }
    }

    // STEP 3: The Crunch (Calculate Mountain Ranges and Ocean Trenches)
    std::cout
        << "[AZGAAR PORT] Calculating Convergent & Divergent Boundaries..."
        << std::endl;

    for (auto &cell : cells) {
      for (int neighbor_idx : cell.neighbors) {
        VoronoiCell &neighbor = cells[neighbor_idx];

        // If we are looking at a border between two different plates
        if (cell.plate_id != neighbor.plate_id) {
          Plate &p1 = plates[cell.plate_id];
          Plate &p2 = plates[neighbor.plate_id];

          float nx = neighbor.x - cell.x;
          float ny = neighbor.y - cell.y;
          float mag = std::sqrt(nx * nx + ny * ny);
          if (mag > 0.0f) {
            nx /= mag;
            ny /= mag;
          }

          float impact =
              CalculateCollisionImpact(p1.dx, p1.dy, p2.dx, p2.dy, nx, ny);

          // DRASTICALLY INCREASE IMPACT TO MAKE JAGGED CONTINENT SHAPES
          if (impact > 0.1f) {
            // Convergent Boundary: CRUNCH! Form a violent mountain range.
            cell.elevation += impact * 1.5f; // Push way up
            if (cell.elevation > 1.0f)
              cell.elevation = 1.0f;
          } else if (impact < -0.1f) {
            // Divergent Boundary: Pulling apart. Form a deep sea trench.
            cell.elevation -= std::abs(impact) * 0.8f; // Push down hard
            if (cell.elevation < 0.0f)
              cell.elevation = 0.0f;
          }
        }
      }
    }

    // STEP 4: Coastal Smoothing (Optional but highly recommended)
    // Runs a simple 3x3 blur kernel over the hexes so mountains smoothly roll
    // down into beaches
    std::cout << "[AZGAAR PORT] Smoothing Coastal Shelves..." << std::endl;
    int smoothing_passes = 3;
    for (int p = 0; p < smoothing_passes; p++) {
      std::vector<float> smoothed_elevation(cells.size());
      for (size_t i = 0; i < cells.size(); i++) {
        float sum = cells[i].elevation;
        int count = 1;
        for (int n : cells[i].neighbors) {
          sum += cells[n].elevation;
          count++;
        }
        smoothed_elevation[i] = sum / (float)count;
      }
      for (size_t i = 0; i < cells.size(); i++) {
        cells[i].elevation = smoothed_elevation[i];
      }
    }

    std::cout << "[AZGAAR PORT] Topology Matrix generated." << std::endl;
  }

  // Helper to convert "NW", "E", etc. from your React UI into actual math
  // vectors
  void GetWindVector(const std::string &dir, float &dx, float &dy) {
    if (dir == "N") {
      dx = 0.0f;
      dy = -1.0f;
    } else if (dir == "NE") {
      dx = 0.7f;
      dy = -0.7f;
    } else if (dir == "E") {
      dx = 1.0f;
      dy = 0.0f;
    } else if (dir == "SE") {
      dx = 0.7f;
      dy = 0.7f;
    } else if (dir == "S") {
      dx = 0.0f;
      dy = 1.0f;
    } else if (dir == "SW") {
      dx = -0.7f;
      dy = 0.7f;
    } else if (dir == "W") {
      dx = -1.0f;
      dy = 0.0f;
    } else if (dir == "NW") {
      dx = -0.7f;
      dy = -0.7f;
    } else {
      dx = 1.0f;
      dy = 0.0f;
    }
  }

  void SimulateClimate(const ClimateRules &climate) {
    std::cout << "[AZGAAR PORT] Simulating Orographic Precipitation & Wind..."
              << std::endl;

    // STEP 1: Base Temperature & Initialization
    // We assume the map Y coordinates go from 0.0 (North Pole) to 1000.0 (South
    // Pole)
    for (auto &cell : cells) {
      float norm_y = cell.y / 1000.0f;

      // Determine which of the 7 wind bands this cell falls into based on its Y
      // coordinate
      int band_index = std::min(6, std::max(0, (int)(norm_y * 7.0f)));

      float dx, dy;
      std::string band_dir = (climate.wind_bands.size() > (size_t)band_index)
                                 ? climate.wind_bands[band_index]
                                 : "E";
      GetWindVector(band_dir, dx, dy);
      cell.wind_dx = dx;
      cell.wind_dy = dy;

      // Base temp based on latitude (Equator is at y=0.5)
      float dist_to_equator =
          std::abs(norm_y - 0.5f) * 2.0f; // 0.0 at equator, 1.0 at poles
      cell.temperature =
          40.0f - (dist_to_equator * 80.0f); // 40C at equator, -40C at poles

      // Altitude Lapse Rate: Temperature drops as elevation rises
      if (cell.elevation > 0.2f) { // 0.2 is our "sea level"
        cell.temperature -= (cell.elevation - 0.2f) * 30.0f;
      }

      // Initialize oceans with max moisture
      if (cell.elevation <= 0.2f) {
        cell.moisture = 1.0f;
      } else {
        cell.moisture = 0.0f;
      }
    }

    // STEP 2: The Wind Raycast (Azgaar's Rain Shadow Math)
    int wind_passes = 15;
    for (int pass = 0; pass < wind_passes; pass++) {
      std::vector<float> next_moisture(cells.size(), 0.0f);

      for (size_t i = 0; i < cells.size(); i++) {
        VoronoiCell &cell = cells[i];

        if (cell.moisture <= 0.01f)
          continue;

        int downwind_neighbor = -1;
        float max_dot = -1.0f;

        for (int n_idx : cell.neighbors) {
          VoronoiCell &neighbor = cells[n_idx];
          float nx = neighbor.x - cell.x;
          float ny = neighbor.y - cell.y;
          // The following lines are misplaced and seem to be part of grid
          // generation, not wind simulation. They are commented out to maintain
          // logical and syntactical correctness within this function. auto&
          // offsets = (c % 2 == 0) ? neighborOffsetsEven : neighborOffsetsOdd;

          // for (int n = 0; n < 6; ++n) {
          //   int nc = c + offsets[n][0];
          //   int nr = r + offsets[n][1];

          //   // TOROIDAL WRAPPING (Spherical Planet)
          //   if (nc < 0) nc += cols;
          //   if (nc >= cols) nc -= cols;

          //   // Wrap poles vertically but don't connect North directly to
          //   South if (nr >= 0 && nr < rows) {
          //     int nIndex = nr * cols + nc;
          //     if (nIndex < cellCount) {
          //        cells[i].neighbors.push_back(nIndex);
          //     }
          //   }
          // }
          float mag = std::sqrt(nx * nx + ny * ny);
          if (mag == 0)
            continue;
          nx /= mag;
          ny /= mag;

          float dot = (nx * cell.wind_dx) + (ny * cell.wind_dy);
          if (dot > max_dot) {
            max_dot = dot;
            downwind_neighbor = n_idx;
          }
        }

        if (downwind_neighbor != -1) {
          VoronoiCell &target = cells[downwind_neighbor];

          // OROGRAPHIC LIFT
          float elevation_diff = target.elevation - cell.elevation;

          if (elevation_diff > 0.0f) {
            float rain_dump =
                std::min(cell.moisture,
                         elevation_diff * 2.5f * climate.rainfall_multiplier);
            cell.moisture -= rain_dump;
            next_moisture[downwind_neighbor] += rain_dump;
          }

          float passed_moisture = cell.moisture * 0.8f;
          next_moisture[downwind_neighbor] += passed_moisture;
        }
      }

      for (size_t i = 0; i < cells.size(); i++) {
        if (cells[i].elevation > 0.2f) {
          cells[i].moisture =
              std::min(1.0f, cells[i].moisture + next_moisture[i]);
        }
      }
    }

    std::cout << "[AZGAAR PORT] Global Weather Matrix stabilized." << std::endl;
  }

  void AssignBiomes(const std::vector<BiomeDef> &biomeDefs) {
    std::cout
        << "Assigning dynamics biomes based on final Whittaker Diagram math..."
        << std::endl;
    for (auto &cell : cells) {
      if (cell.elevation <= 0.2f) {
        cell.biome_tag = "OCEAN";
        continue;
      }

      cell.biome_tag = "WASTELAND"; // Default fallback

      for (const auto &b : biomeDefs) {
        if (cell.temperature >= b.temp_range.first &&
            cell.temperature <= b.temp_range.second &&
            cell.moisture >= b.rain_range.first &&
            cell.moisture <= b.rain_range.second) {
          cell.biome_tag = b.name;
          break; // Found a match
        }
      }
    }
  }
};
