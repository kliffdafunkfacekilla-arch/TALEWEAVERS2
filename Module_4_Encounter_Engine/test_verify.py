import sys
import os

# Add the directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import generate_encounter
import asyncio

async def test_generator():
    biomes = ["Forest", "Dungeon", "Urban", "Desert"]
    print("Testing Encounter Generator...")
    for biome in biomes:
        for threat in [1, 5, 10]:
            try:
                encounter = await generate_encounter(biome=biome, threat_level=threat)
                print(f"[{biome} - Threat {threat}] Generated: {encounter.type} - {encounter.name}")
            except Exception as e:
                print(f"Error generating for {biome} - {threat}: {e}")

if __name__ == "__main__":
    asyncio.run(test_generator())
