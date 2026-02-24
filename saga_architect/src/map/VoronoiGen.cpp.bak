#include "core/Types.h"
#include <iostream>
#include <vector>


/**
 * @brief Handles Tectonic plates and polygon relaxation.
 *
 * Generation: Scatter 20,000 points. Use jc_voronoi to build polygons.
 * Tectonics: Pick 10 random cells as plate centers. Expand outward.
 * Where Plate A meets Plate B, push elevation to 1.0 (Mountains).
 * Where they pull apart, drop to 0.0 (Ocean).
 */
class VoronoiGen {
public:
  void GenerateBaseMap(int cellCount) {
    std::cout << "Generating " << cellCount << " Voronoi cells..." << std::endl;
    // TODO: Integrate jc_voronoi for polygon generation
  }

  void SimulateTectonics(int plateCount) {
    std::cout << "Simulating " << plateCount << " tectonic plates..."
              << std::endl;
    // TODO: Implement plate expansion and elevation logic
  }

  void AssignBiomes(const std::vector<BiomeDef> &biomeDefs) {
    std::cout << "Assigning biomes based on temp/moisture..." << std::endl;
    // TODO: Loop through cells and match against BiomeDef temp/rain ranges
  }

private:
  std::vector<VoronoiCell> cells;
};
