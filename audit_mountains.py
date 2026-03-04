import json
import os

path = r"C:\Users\krazy\Documents\GitHub\TALEWEAVERS\saga_architect\Saga_Master_World.json"
if not os.path.exists(path):
    print("File not found")
    exit()

with open(path, "r") as f:
    data = json.load(f)
    map_data = data.get("macro_map", [])
    
    found = False
    for cell in map_data:
        if cell.get("elevation", 0) > 0.82:
            print(f"FOUND: Hex #{cell.get('id')} | Elevation: {cell.get('elevation')} | Biome Tag: {cell.get('biome_tag')}")
            found = True
            # Just find the first few
            break
            
    if not found:
        # Check some other elevations to see what's happening
        print("No hex > 0.82 found. Checking highest elevation available...")
        max_elev = max(c.get("elevation", 0) for c in map_data)
        print(f"Max Elevation found: {max_elev}")
        for cell in map_data:
            if cell.get("elevation", 0) == max_elev:
                 print(f"Highest Hex: Hex #{cell.get('id')} | Elevation: {cell.get('elevation')} | Biome Tag: {cell.get('biome_tag')}")
                 break
