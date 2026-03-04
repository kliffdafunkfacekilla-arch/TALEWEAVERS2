#include "../../deps/nlohmann/json.hpp"
#include "../core/Types.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>

#include <numeric>
#include <queue>
#include <random>
#include <vector>

// Include stb_image for PNG reading
#define STB_IMAGE_IMPLEMENTATION
#include "../stb_image.h"

// Include Delaunator for true Voronoi Topology
#include "../../deps/delaunator/delaunator.hpp"

class VoronoiGen {
public:
  std::vector<VoronoiCell> cells;
  std::vector<VoronoiCell> local_cells_cache; // Storage for subgrid logic
  float worldWidth = 1000.0f;
  float worldHeight = 1000.0f;

  void GenerateBaseMap(int cellCount, float w = 1000.0f, float h = 1000.0f) {
    this->worldWidth = w;
    this->worldHeight = h;
    std::cout << "Generating " << cellCount << " cells in a " << worldWidth
              << "x" << worldHeight << " space..." << std::endl;
    cells.resize(cellCount);

    // If it's a square count, or specifically planetary dimensions (630x630 or
    // 1000x400)
    int side = static_cast<int>(std::sqrt(cellCount));
    if (side * side == cellCount || (worldWidth == 630 && worldHeight == 630) ||
        (worldWidth == 1000 && worldHeight == 400)) {
      int cols = static_cast<int>(worldWidth);
      int rows = static_cast<int>(worldHeight);

      std::cout << "[INFO] Planetary Scale detected (" << cols << "x" << rows
                << "). Generating Hexagonal Grid..." << std::endl;

      for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
          int i = r * cols + c;
          if (i >= cellCount)
            break;
          cells[i].id = i;
          // Hexagonal offset: every other row is shifted
          float x_offset = (r % 2 == 0) ? 0.0f : 0.5f;
          cells[i].x = (static_cast<float>(c) + x_offset);
          cells[i].y =
              static_cast<float>(r) * 0.866f; // sqrt(3)/2 for equilateral hexes

          cells[i].elevation = 0.2f;
          cells[i].temperature = 20.0f;
          cells[i].moisture = 0.5f;
        }
      }

      // Establish Hex Neighbors (6-way connectivity)
      for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
          int i = r * cols + c;
          if (i >= cellCount)
            break;

          // neighbor offsets depending on even/odd row
          int oddRow = r % 2;
          int n_offsets[6][2] = {
              {-1, 0},          {1, 0},       // Left, Right
              {oddRow - 1, -1}, {oddRow, -1}, // Top-Left, Top-Right
              {oddRow - 1, 1},  {oddRow, 1}   // Bottom-Left, Bottom-Right
          };

          for (int n = 0; n < 6; ++n) {
            int nc = c + n_offsets[n][0];
            int nr = r + n_offsets[n][1];

            // Horizontal wrapping (Spherical planet)
            if (nc < 0)
              nc = cols - 1;
            if (nc >= cols)
              nc = 0;

            if (nr >= 0 && nr < rows) {
              cells[i].neighbors.push_back(nr * cols + nc);
            }
          }
        }
      }
    } else {
      // Fallback to random Voronoi
      for (int i = 0; i < cellCount; ++i) {
        cells[i].id = i;
        cells[i].x = static_cast<float>(rand() % (int)worldWidth);
        cells[i].y = static_cast<float>(rand() % (int)worldHeight);
        cells[i].elevation = 0.2f;
        cells[i].temperature = 20.0f;
        cells[i].moisture = 0.5f;
      }

      std::vector<double> coords;
      for (const auto &c : cells) {
        coords.push_back(c.x);
        coords.push_back(c.y);
      }

      delaunator::Delaunator d(coords);
      for (std::size_t i = 0; i < d.triangles.size(); i += 3) {
        int t0 = d.triangles[i];
        int t1 = d.triangles[i + 1];
        int t2 = d.triangles[i + 2];
        if (std::find(cells[t0].neighbors.begin(), cells[t0].neighbors.end(),
                      t1) == cells[t0].neighbors.end())
          cells[t0].neighbors.push_back(t1);
        if (std::find(cells[t0].neighbors.begin(), cells[t0].neighbors.end(),
                      t2) == cells[t0].neighbors.end())
          cells[t0].neighbors.push_back(t2);
        if (std::find(cells[t1].neighbors.begin(), cells[t1].neighbors.end(),
                      t0) == cells[t1].neighbors.end())
          cells[t1].neighbors.push_back(t0);
        if (std::find(cells[t1].neighbors.begin(), cells[t1].neighbors.end(),
                      t2) == cells[t1].neighbors.end())
          cells[t1].neighbors.push_back(t2);
        if (std::find(cells[t2].neighbors.begin(), cells[t2].neighbors.end(),
                      t0) == cells[t2].neighbors.end())
          cells[t2].neighbors.push_back(t0);
        if (std::find(cells[t2].neighbors.begin(), cells[t2].neighbors.end(),
                      t1) == cells[t2].neighbors.end())
          cells[t2].neighbors.push_back(t1);
      }
    }
    std::cout << "Topology graph established." << std::endl;
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
      int px = static_cast<int>((cell.x / worldWidth) * width);
      int py = static_cast<int>((cell.y / worldHeight) * height);
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
    std::uniform_real_distribution<float> rand_x(
        step.range_x.first * worldWidth, step.range_x.second * worldWidth);
    std::uniform_real_distribution<float> rand_y(
        step.range_y.first * worldHeight, step.range_y.second * worldHeight);
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
    std::uniform_real_distribution<float> rand_x(
        step.range_x.first * worldWidth, step.range_x.second * worldWidth);
    std::uniform_real_distribution<float> rand_y(
        step.range_y.first * worldHeight, step.range_y.second * worldHeight);
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
    std::uniform_real_distribution<float> rand_x(
        step.range_x.first * worldWidth, step.range_x.second * worldWidth);
    std::uniform_real_distribution<float> rand_y(
        step.range_y.first * worldHeight, step.range_y.second * worldHeight);
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
      float map_center_x = worldWidth / 2.0f;
      float map_center_y = worldHeight / 2.0f;
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
      float norm_y = cell.y / (worldHeight * 0.866f);

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

  void SimulateHydrology() {
    std::cout << "[AZGAAR PORT] Simulating Hydrology (Water Flow)..."
              << std::endl;

    // 1. Reset and initialization
    for (auto &cell : cells) {
      cell.flow_accumulation = 0.0f;
      cell.has_river = false;
      cell.river_next_id = -1;
    }

    // 2. Sort cells by elevation (highest to lowest) to ensure single-pass flow
    std::vector<int> indices(cells.size());
    std::iota(indices.begin(), indices.end(), 0);
    std::sort(indices.begin(), indices.end(), [&](int a, int b) {
      return cells[a].elevation > cells[b].elevation;
    });

    // 3. Downhill routing
    for (int idx : indices) {
      VoronoiCell &cell = cells[idx];
      if (cell.elevation <= 0.2f)
        continue; // Oceans absorb flow

      int lowest_neighbor = -1;
      float min_elevation = cell.elevation;

      for (int n_idx : cell.neighbors) {
        if (cells[n_idx].elevation < min_elevation) {
          min_elevation = cells[n_idx].elevation;
          lowest_neighbor = n_idx;
        }
      }

      if (lowest_neighbor != -1) {
        cell.river_next_id = lowest_neighbor;
        // Pass raw moisture + accumulated flow to neighbor
        cells[lowest_neighbor].flow_accumulation +=
            (cell.moisture * 0.1f) + cell.flow_accumulation;
      }
    }

    // 4. River thresholding
    float river_threshold = 0.5f; // Adjust based on desired river density
    for (auto &cell : cells) {
      if (cell.flow_accumulation > river_threshold && cell.elevation > 0.2f) {
        cell.has_river = true;
        cell.river_size = std::min(5.0f, cell.flow_accumulation * 2.0f);
      }
    }

    std::cout << "[AZGAAR PORT] Hydrology Simulation Complete." << std::endl;
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

      // MOUNTAIN check: High elevation peaks get MOUNTAIN tag priority
      if (cell.elevation > 0.70f) {
        cell.biome_tag = "MOUNTAIN";
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

  // --- TIER 4: LOCAL EXPLORATION ZONE GENERATION ---
  // Generates a 96x96 sub-grid for a specific macro-hex, using neighbors for
  // interpolation.
  void GenerateSubGrid(int parent_id, int grid_size = 96) {
    if (parent_id < 0 || parent_id >= (int)cells.size())
      return;

    VoronoiCell &center = cells[parent_id];
    std::vector<int> cluster = center.neighbors;
    cluster.push_back(parent_id);

    std::cout << "[TIER 4] Generating " << grid_size << "x" << grid_size
              << " Local Zone for Hex #" << parent_id << "..." << std::endl;

    // 1. Find River Source and Sink
    int source_id = -1;
    for (int n_idx : center.neighbors) {
      if (cells[n_idx].river_next_id == parent_id) {
        source_id = n_idx;
        break; // Prototype: assume one main source
      }
    }
    int sink_id = center.river_next_id;

    // Calculate normalized entry/exit relative to center (0.5, 0.5)
    auto get_edge_pos = [&](int neighbor_id) -> std::pair<float, float> {
      if (neighbor_id == -1)
        return {0.5f, 0.5f};
      float dx = cells[neighbor_id].x - center.x;
      float dy = (cells[neighbor_id].y - center.y) * 0.866f;
      float mag = std::sqrt(dx * dx + dy * dy);
      if (mag == 0)
        return {0.5f, 0.5f};
      // Return point on the edge (distance 0.5 from center in normalized hex)
      return {0.5f + (dx / mag) * 0.5f, 0.5f + (dy / mag) * 0.5f};
    };

    std::pair<float, float> entry = get_edge_pos(source_id);
    std::pair<float, float> exit = get_edge_pos(sink_id);

    // 2. Generate Local Data
    local_cells_cache.clear();
    local_cells_cache.resize(grid_size * grid_size);

    for (int y = 0; y < grid_size; ++y) {
      for (int x = 0; x < grid_size; ++x) {
        int idx = y * grid_size + x;
        local_cells_cache[idx].id = idx;
        local_cells_cache[idx].x = (float)x;
        local_cells_cache[idx].y = (float)y;

        float nx = (float)x / (float)grid_size;
        float ny = (float)y / (float)grid_size;

        // --- INTERPOLATION (IDW) ---
        float total_weight = 0.0f;
        float interp_elevation = 0.0f;
        float interp_moisture = 0.0f;

        float wx = center.x + (nx - 0.5f);
        float wy = center.y + (ny - 0.5f) / 0.866f;

        for (int neighbor_id : cluster) {
          VoronoiCell &n = cells[neighbor_id];
          float dx = n.x - wx;
          float dy = n.y - wy;
          float dist_sq = dx * dx + dy * dy;
          if (dist_sq < 0.01f)
            dist_sq = 0.01f;

          float w = 1.0f / dist_sq;
          total_weight += w;
          interp_elevation += n.elevation * w;
          interp_moisture += n.moisture * w;
        }

        float base_elevation = interp_elevation / total_weight;
        float base_moisture = interp_moisture / total_weight;

        // --- ORGANIC NOISE ---
        float noise = (float)(rand() % 100) / 1000.0f;
        local_cells_cache[idx].elevation =
            std::min(1.0f, base_elevation + noise);
        local_cells_cache[idx].moisture =
            std::min(1.0f, base_moisture + (noise * 0.2f));

        // --- RIVER CARVING (Spline Logic) ---
        if (center.has_river) {
          // check distance to line segment (entry -> exit)
          float line_dx = exit.first - entry.first;
          float line_dy = exit.second - entry.second;
          float line_mag_sq = line_dx * line_dx + line_dy * line_dy;
          if (line_mag_sq > 0) {
            float t =
                std::max(0.0f, std::min(1.0f, ((nx - entry.first) * line_dx +
                                               (ny - entry.second) * line_dy) /
                                                  line_mag_sq));
            float proj_x = entry.first + t * line_dx;
            float proj_y = entry.second + t * line_dy;

            // Add "Wiggle" (Winding river)
            proj_x += std::sin(t * 10.0f) * 0.02f;
            proj_y += std::cos(t * 10.0f) * 0.02f;

            float dist_to_river =
                std::sqrt(std::pow(nx - proj_x, 2) + std::pow(ny - proj_y, 2));
            if (dist_to_river < 0.02f) {
              local_cells_cache[idx].biome_tag = "LOCAL_RIVER";
              local_cells_cache[idx].elevation -= 0.1f; // Carve bed
            } else {
              local_cells_cache[idx].biome_tag = center.biome_tag;
            }
          } else { // If line_mag_sq is 0, it means entry and exit are the same
                   // point.
            local_cells_cache[idx].biome_tag = center.biome_tag;
          }
        } else {
          local_cells_cache[idx].biome_tag = center.biome_tag;
        }

        // --- ROAD CARVING (Spline Logic) ---
        if (center.has_road) {
          int road_source_id = -1;
          for (int n_idx : center.neighbors) {
            if (cells[n_idx].road_next_id == parent_id) {
              road_source_id = n_idx;
              break;
            }
          }
          int road_sink_id = center.road_next_id;

          std::pair<float, float> r_entry = get_edge_pos(road_source_id);
          std::pair<float, float> r_exit = get_edge_pos(road_sink_id);

          float r_line_dx = r_exit.first - r_entry.first;
          float r_line_dy = r_exit.second - r_entry.second;
          float r_line_mag_sq = r_line_dx * r_line_dx + r_line_dy * r_line_dy;
          if (r_line_mag_sq > 0) {
            float t = std::max(
                0.0f, std::min(1.0f, ((nx - r_entry.first) * r_line_dx +
                                      (ny - r_entry.second) * r_line_dy) /
                                         r_line_mag_sq));
            float r_proj_x = r_entry.first + t * r_line_dx;
            float r_proj_y = r_entry.second + t * r_line_dy;

            // Different Jitter for roads
            r_proj_x += std::cos(t * 8.0f) * 0.015f;
            r_proj_y += std::sin(t * 8.0f) * 0.015f;

            float dist_to_road = std::sqrt(std::pow(nx - r_proj_x, 2) +
                                           std::pow(ny - r_proj_y, 2));
            if (dist_to_road < 0.01f) {
              local_cells_cache[idx].settlement_name = "TRADE_ROUTE";
              local_cells_cache[idx].elevation =
                  std::max(local_cells_cache[idx].elevation,
                           0.25f); // Roads are flat/raised
            }
          }
        }

        // --- STRUCTURE LOGIC ---
        if (!center.settlement_name.empty()) {
          bool is_high_ground = local_cells_cache[idx].elevation > 0.7f;
          bool near_water = local_cells_cache[idx].moisture > 0.6f ||
                            local_cells_cache[idx].biome_tag == "LOCAL_RIVER";
          bool near_road =
              local_cells_cache[idx].settlement_name == "TRADE_ROUTE";

          if (is_high_ground) {
            local_cells_cache[idx].settlement_name = "STRATEGIC_DEFENSE";
          } else if ((near_water || near_road) &&
                     local_cells_cache[idx].elevation < 0.4f) {
            local_cells_cache[idx].settlement_name = "SETTLEMENT_HUB";
          } else if (center.biome_tag == "MOUNTAIN") {
            local_cells_cache[idx].settlement_name = "MINING_OPERATION";
          }
        }
      }
    }
    std::cout << "[TIER 4] Local Grid generated with River & Road Splines."
              << std::endl;
    ExportSubGrid(parent_id);
  }

  void ExportSubGrid(int parent_id) {
    std::string filename = "subgrid_hex_" + std::to_string(parent_id) + ".json";
    ExportSubGrid(filename);
  }

  void ExportSubGrid(const std::string &filename) {
    nlohmann::json output;
    output["grid_size"] = 96;
    output["nodes"] = nlohmann::json::array();

    for (const auto &node : local_cells_cache) {
      nlohmann::json n;
      n["id"] = node.id;
      n["x"] = node.x;
      n["y"] = node.y;
      n["elevation"] = node.elevation;
      n["moisture"] = node.moisture;
      n["biome"] = node.biome_tag;
      n["settlement"] = node.settlement_name;
      n["is_visible"] = node.is_visible;
      n["is_explored"] = node.is_explored;
      n["has_entity"] = node.has_entity;
      n["entity_type"] = node.entity_type;
      n["detection_radius"] = node.detection_radius;
      n["is_alerted"] = node.is_alerted;
      n["market_state"] = node.market_state;
      n["production_rate"] = node.production_rate;
      output["nodes"].push_back(n);
    }

    std::ofstream f(filename);
    if (f.is_open()) {
      f << output.dump(4);
      std::cout << "[TIER 4] Exported Local SubGrid to " << filename
                << std::endl;
    } else {
      std::cerr << "[TIER 4] Error: Could not open file " << filename
                << " for writing." << std::endl;
    }
  }
};
