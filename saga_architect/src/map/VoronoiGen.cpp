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

  void SimulateTectonics(int plateCount) {
    std::cout << "Simulating " << plateCount << " tectonic plates..."
              << std::endl;
    if (cells.empty())
      return;

    std::vector<int> plate_assignments(cells.size(), -1);
    std::queue<int> frontier;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, cells.size() - 1);

    for (int i = 0; i < plateCount; ++i) {
      int seed = dis(gen);
      plate_assignments[seed] = i;
      frontier.push(seed);
    }

    while (!frontier.empty()) {
      int current = frontier.front();
      frontier.pop();
      int my_plate = plate_assignments[current];

      for (int neighbor_id : cells[current].neighbors) {
        if (plate_assignments[neighbor_id] == -1) {
          plate_assignments[neighbor_id] = my_plate;
          frontier.push(neighbor_id);
        } else if (plate_assignments[neighbor_id] != my_plate) {
          bool is_convergent = (rand() % 100) > 40;
          if (is_convergent) {
            cells[current].elevation =
                std::min(1.0f, cells[current].elevation + 0.4f);
            cells[neighbor_id].elevation =
                std::min(1.0f, cells[neighbor_id].elevation + 0.4f);
          } else {
            cells[current].elevation =
                std::max(0.0f, cells[current].elevation - 0.3f);
            cells[neighbor_id].elevation =
                std::max(0.0f, cells[neighbor_id].elevation - 0.3f);
          }
        }
      }
    }
  }

  // Atmospheric Physics — wind bands, pole-equator temperature, rain shadow
  // simulation
  void SimulateClimate(const ClimateRules &climate) {
    std::cout << "[INFO] Simulating Atmospheric Physics (Wind & Rain)...\n";

    // 1. Direction Mapping (N, NE, E, SE, S, SW, W, NW) -> (dx, dy)
    std::map<std::string, std::pair<float, float>> dir_map = {
        {"N", {0.0f, -1.0f}}, {"NE", {1.0f, -1.0f}}, {"E", {1.0f, 0.0f}},
        {"SE", {1.0f, 1.0f}}, {"S", {0.0f, 1.0f}},   {"SW", {-1.0f, 1.0f}},
        {"W", {-1.0f, 0.0f}}, {"NW", {-1.0f, -1.0f}}};

    // 2. Base Temperatures & Wind Assignment
    for (auto &cell : cells) {
      // Latitude scale from 0.0 (North Pole) to 0.5 (Equator) to 1.0 (South
      // Pole)
      float lat = cell.y / 1000.0f;

      // Calculate Temperature via Interpolation
      if (lat <= 0.5f) {
        // Northern Hemisphere: Blend North Pole to Equator
        float t = lat / 0.5f;
        float pole_avg =
            (climate.north_pole_temp.first + climate.north_pole_temp.second) /
            2.0f;
        float eq_avg =
            (climate.equator_temp.first + climate.equator_temp.second) / 2.0f;
        cell.temperature = pole_avg + (t * (eq_avg - pole_avg));
      } else {
        // Southern Hemisphere: Blend Equator to South Pole
        float t = (lat - 0.5f) / 0.5f;
        float eq_avg =
            (climate.equator_temp.first + climate.equator_temp.second) / 2.0f;
        float pole_avg =
            (climate.south_pole_temp.first + climate.south_pole_temp.second) /
            2.0f;
        cell.temperature = eq_avg + (t * (pole_avg - eq_avg));
      }

      // Elevation decreases temperature drastically
      cell.temperature -= (cell.elevation * 20.0f);

      // Assign Wind Band (7 bands total)
      int band_index = std::min(6, static_cast<int>(lat * 7.0f));
      std::string wind_dir =
          climate.wind_bands.size() > static_cast<size_t>(band_index)
              ? climate.wind_bands[band_index]
              : "E";
      cell.wind_dx = dir_map[wind_dir].first;
      cell.wind_dy = dir_map[wind_dir].second;

      // Initialize Base Moisture (Oceans are 1.0, Land is 0.0)
      cell.moisture = (cell.elevation <= 0.05f) ? 1.0f : 0.0f;
    }

    // 3. Rain Shadow Simulation (Cellular Automata)
    int simulation_steps = 15;
    for (int step = 0; step < simulation_steps; ++step) {
      std::vector<float> next_moisture(cells.size(), 0.0f);

      for (size_t i = 0; i < cells.size(); ++i) {
        next_moisture[i] = cells[i].moisture;

        if (cells[i].elevation <= 0.05f)
          continue; // Oceans stay 1.0

        float incoming_rain = 0.0f;
        for (int n_id : cells[i].neighbors) {
          float dx = cells[i].x - cells[n_id].x;
          float dy = cells[i].y - cells[n_id].y;

          float length = std::sqrt(dx * dx + dy * dy);
          if (length > 0) {
            dx /= length;
            dy /= length;
          }

          // Dot product: If > 0.5, the wind is blowing from them to us
          float dot = (dx * cells[i].wind_dx) + (dy * cells[i].wind_dy);

          if (dot > 0.5f) {
            float moisture_passed = cells[n_id].moisture * 0.9f;

            // RAIN SHADOW: Mountains block 80% of rain!
            if (cells[n_id].elevation > 0.6f) {
              moisture_passed *= 0.2f;
            }

            incoming_rain = std::max(incoming_rain, moisture_passed);
          }
        }
        next_moisture[i] = std::max(next_moisture[i], incoming_rain);
      }
      for (size_t i = 0; i < cells.size(); ++i) {
        cells[i].moisture = next_moisture[i];
      }
    }

    // 4. Apply Global Rainfall Multiplier
    for (auto &cell : cells) {
      if (cell.elevation > 0.05f) {
        cell.moisture *= climate.rainfall_multiplier;
        cell.moisture = std::min(1.0f, std::max(0.0f, cell.moisture));
      }
    }
  }

  void AssignBiomes(const std::vector<BiomeDef> &biomeDefs) {
    std::cout << "Assigning biomes based on temp/moisture..." << std::endl;

    for (auto &cell : cells) {
      // Temperature and moisture are now set by SimulateClimate()
      // Just match against biome rules
      cell.biome_tag = "WASTELAND"; // Fallback
      for (const auto &def : biomeDefs) {
        if (cell.temperature >= def.temp_range.first &&
            cell.temperature <= def.temp_range.second &&
            cell.moisture >= def.rain_range.first &&
            cell.moisture <= def.rain_range.second) {
          cell.biome_tag = def.name;
          break;
        }
      }
      if (cell.elevation <= 0.05f) {
        cell.biome_tag = "OCEAN";
      }
    }
  }
};
