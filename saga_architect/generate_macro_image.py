import json
import os
from PIL import Image

def get_biome_color(biome_tag: str, elevation: float) -> tuple:
    # Colors matching the Vivid Tier 2 renderer in MapRenderer.tsx
    if elevation <= 0.2:
        return (15, 23, 42) if elevation < 0.1 else (2, 132, 199)
        
    colors = {
        'GLACIER': (241, 245, 249),
        'TUNDRA': (148, 163, 184),
        'TAIGA': (71, 85, 105),
        'STEPPE': (180, 83, 9),
        'GRASSLAND': (74, 222, 128),
        'TEMPERATE_FOREST': (22, 101, 52),
        'HOT_DESERT': (250, 204, 21),
        'SAVANNA': (234, 179, 8),
        'TROPICAL_RAINFOREST': (6, 78, 59),
        'MOUNTAIN': (63, 63, 70)
    }
    
    # Mountain priority check, just like MapRenderer
    if biome_tag == 'MOUNTAIN' or elevation > 0.70:
        return colors['MOUNTAIN']
        
    return colors.get(biome_tag, (34, 197, 94)) # Default green

def generate_macro_image():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "Saga_Master_World.json")
    output_dir = os.path.join(base_dir, "static")
    output_path = os.path.join(output_dir, "macro_map.webp")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(input_path):
        print(f"[MACRO MAP] Input file {input_path} not found.")
        return

    print("[MACRO MAP] Loading world data...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    macro_map = data.get("macro_map", [])
    if not macro_map:
        print("[MACRO MAP] No macro_map data found.")
        return

    print(f"[MACRO MAP] Processing {len(macro_map)} hexes...")

    # Determine bounds
    min_x = min(cell.get("x", 0) for cell in macro_map)
    max_x = max(cell.get("x", 0) for cell in macro_map)
    min_y = min(cell.get("y", 0) for cell in macro_map)
    max_y = max(cell.get("y", 0) for cell in macro_map)

    # Add a little padding and ensure sizes make sense
    width = int(max_x - min_x) + 10
    height = int(max_y - min_y) + 10

    # Increase resolution slightly by multiplying coordinates
    scale = 2
    img_width = width * scale
    img_height = height * scale

    # Create image
    img = Image.new("RGB", (img_width, img_height), (5, 5, 5)) # Dark background
    pixels = img.load()

    # Draw hexes as small blobs
    for cell in macro_map:
        x = int((cell.get("x", 0) - min_x) * scale) + 5 * scale
        y = int((cell.get("y", 0) - min_y) * scale) + 5 * scale
        
        color = get_biome_color(cell.get("biome_tag", ""), cell.get("elevation", 0))
        
        # Draw a small 2x2 or 3x3 pixel blip for each hex center
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = x + dx, y + dy
                if 0 <= nx < img_width and 0 <= ny < img_height:
                    pixels[nx, ny] = color

    print(f"[MACRO MAP] Saving image to {output_path} ({img_width}x{img_height})...")
    img.save(output_path, "WEBP", quality=80)
    print("[MACRO MAP] Done.")

if __name__ == "__main__":
    generate_macro_image()
