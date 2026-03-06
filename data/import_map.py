import sys
import os
import json
import logging
from pathlib import Path

# Try to import PIL for image processing.
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: PIL (Pillow) is not installed. Image import (.png/.jpg) will not work.")
    print("To fix, run: pip install Pillow")

logging.basicConfig(level=logging.INFO, format="[MAP IMPORTER] %(message)s")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "Saga_Master_World.json"

# Example biome color mapping for image reading 
# Format: (R, G, B): "Biome_Name"
COLOR_TO_BIOME = {
    (34, 139, 34): "Forest",        # Forest Green
    (85, 107, 47): "Swamp",         # Dark Olive
    (210, 180, 140): "Desert",      # Tan
    (245, 245, 245): "Tundra",      # White/Snow
    (139, 137, 137): "Mountain",    # Gray
    (65, 105, 225): "Ocean",        # Blue
    (0, 191, 255): "River",         # Light Blue
    (124, 252, 0): "Grassland"      # Lawn Green
}

def closest_color(rgb):
    """Finds the closest biome mapped color using Euclidean distance."""
    r, g, b = rgb[:3]
    color_diffs = []
    for color_value, biome in COLOR_TO_BIOME.items():
        cr, cg, cb = color_value
        color_diff = sum([abs(r - cr), abs(g - cg), abs(b - cb)])
        color_diffs.append((color_diff, biome))
    return min(color_diffs)[1]

def process_image(filepath: str):
    """Processes a PNG/JPG replacing the grid based on pixels."""
    if not HAS_PIL:
        logging.error("Pillow is not installed. Cannot process images.")
        sys.exit(1)
        
    logging.info(f"Processing Image: {filepath}")
    
    try:
        img = Image.open(filepath)
        # Convert to RGB to ensure no alpha channel issues
        img = img.convert("RGB")
        
        # Max resolution safety - we don't want a 4k image resulting in 8 million JSON nodes
        max_width = 200
        max_height = 200
        
        if img.width > max_width or img.height > max_height:
            logging.info(f"Image too large ({img.width}x{img.height}). Downscaling to {max_width}x{max_height} max.")
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
        pixels = img.load()
        width, height = img.size
        
        macro_map = []
        cell_id = 1
        
        for y in range(height):
            for x in range(width):
                rgb = pixels[x, y]
                biome = closest_color(rgb)
                
                cell_data = {
                    "cell_id": cell_id,
                    "x_coord": x,
                    "y_coord": y,
                    "biome": biome,
                    "threat_level": 1,
                    "faction_owner": "None",
                    "tags": []
                }
                macro_map.append(cell_data)
                cell_id += 1
                
        output_data = {
            "world_name": "Imported Image World",
            "width": width,
            "height": height,
            "macro_map": macro_map
        }
        
        write_output(output_data)
        logging.info(f"Successfully processed {width}x{height} image map into {len(macro_map)} cells.")

    except Exception as e:
        logging.error(f"Failed to process image: {e}")

def process_azgaar(filepath: str):
    """Processes an Azgaar .map text file."""
    logging.info(f"Processing Azgaar Map: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Azgaar separates its internal data arrays piece-by-piece
        lines = content.splitlines()
        
        if len(lines) < 20:
            logging.error("File does not appear to be a valid Azgaar .map version.")
            sys.exit(1)
            
        logging.info("Located data arrays within file.")
        
        # Try to parse the cell biomes, which is typically stored as a string array of integers
        # E.g. [1, 1, 1, 4, 4, 3...] where numbers correspond to their internal biome enum.
        # Note: Azgaar versions vary heavily. This is a generic approach.
        
        # We will scan lines for known JSON array structures if the standard line index moves.
        biomes_line = lines[17] if len(lines) > 17 else "[]"
        
        # Parse it safely
        try:
            biomes_data = json.loads(biomes_line)
        except:
            biomes_data = []
            
        # Fallback if the standard line parse failed
        if not biomes_data or not isinstance(biomes_data, list):
            logging.warning("Standard biome array missing or moved. Generating generic structure.")
            biomes_data = [1] * 1000 # dummy data
            
        # Azgaar Biome Enum Translation (Approximate)
        AZGAAR_BIOMES = {
            1: "Ocean", 2: "Ocean", 3: "Lake", 4: "Forest", 5: "Desert", 
            6: "Savanna", 7: "Tropical Forest", 8: "Swamp", 9: "Mountain", 10: "Tundra"
        }
        
        macro_map = []
        
        # Generate cell nodes
        for idx, biome_val in enumerate(biomes_data):
            biome_name = AZGAAR_BIOMES.get(biome_val, "Grassland")
            
            macro_map.append({
                "cell_id": idx + 1,
                "biome": biome_name,
                "threat_level": 1, # Base
                "faction_owner": "None",
                "tags": ["azgaar_imported"]
            })
            
        output_data = {
            "world_name": "Azgaar Imported World",
            "macro_map": macro_map
        }
        
        write_output(output_data)
        logging.info(f"Successfully processed Azgaar map into {len(macro_map)} cells.")
        
    except Exception as e:
        logging.error(f"Failed to process Azgaar map: {e}")

def write_output(data: dict):
    """Writes the compiled data to the master JSON file."""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved generated SAGA data to: {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_map.py <path_to_map_file>")
        print("Supported formats: .map (Azgaar), .png, .jpg")
        sys.exit(1)
        
    target_file = sys.argv[1]
    
    if not os.path.exists(target_file):
        logging.error(f"File not found: {target_file}")
        sys.exit(1)
        
    ext = Path(target_file).suffix.lower()
    
    if ext == ".map":
        process_azgaar(target_file)
    elif ext in [".png", ".jpg", ".jpeg"]:
        process_image(target_file)
    else:
        logging.error(f"Unsupported file extension: {ext}. Need .map or .png")
        sys.exit(1)
