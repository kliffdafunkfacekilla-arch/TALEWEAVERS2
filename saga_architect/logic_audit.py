import json
import math

def audit_world(filepath):
    print(f"--- Auditing World Data: {filepath} ---")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    macro_map = data.get("macro_map", [])
    if not macro_map:
        print("No macro_map found.")
        return

    cells = {cell['id']: cell for cell in macro_map}
    
    uphill_rivers = 0
    biome_clashes = 0
    total_rivers = 0
    
    clash_rules = {
        "DEEP_TUNDRA": ["SCORCHED_DESERT", "LUSH_JUNGLE"],
        "SCORCHED_DESERT": ["DEEP_TUNDRA", "MUSHROOM_SWAMP"],
        "LUSH_JUNGLE": ["DEEP_TUNDRA"],
        "MUSHROOM_SWAMP": ["SCORCHED_DESERT"]
    }

    for cell_id, cell in cells.items():
        # 1. Audit Rivers
        if cell.get("has_river"):
            total_rivers += 1
            next_id = cell.get("river_next_id", -1)
            if next_id in cells:
                next_cell = cells[next_id]
                # High-precision check (Azgaar math can have tiny rounding)
                if next_cell['elevation'] > cell['elevation'] + 0.001:
                    uphill_rivers += 1
                    if uphill_rivers < 5: # Limit logging
                        print(f"  [RIVER] Uphill Flow: Hex #{cell_id} ({cell['elevation']:.3f}) -> Hex #{next_id} ({next_cell['elevation']:.3f})")

        # 2. Audit Biomes
        biome = cell.get("biome")
        if biome in clash_rules:
            # We need neighbors to check clashes. 
            # In the JSON, we don't have neighbors list anymore to save space (it's reconstructed by topology).
            # Wait, I should check if neighbors list is exported.
            pass

    print(f"\nAudit Results:")
    print(f"  Total Rivers Checked: {total_rivers}")
    print(f"  Uphill River Errors: {uphill_rivers}")
    if uphill_rivers == 0:
        print("  [SUCCESS] All rivers flow downhill or to oceans.")
    else:
        print(f"  [WARNING] Found {uphill_rivers} uphill flow issues.")

if __name__ == "__main__":
    audit_world('Saga_Master_World.json')
