import os
import json
import math
from PIL import Image

# Configuration
ASSET_DIRS = [
    "public/floor",
    "public/tiles",
    "public/objects",
    "public/trees",
    "public/traps",
    "public/water"
]
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_IMAGE = os.path.join(ROOT_DIR, "saga_asset_foundry", "storage", "atlas.png")
OUTPUT_JSON = os.path.join(ROOT_DIR, "saga_asset_foundry", "storage", "atlas.json")
TILE_SIZE = 256 # Normalize to this for the atlas if possible, or keep original

def generate_atlas():
    images = []
    
    # 1. Collect all images
    for sub_dir in ASSET_DIRS:
        full_path = os.path.join(ROOT_DIR, sub_dir)
        if not os.path.exists(full_path):
            continue
            
        for root, _, files in os.walk(full_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(root, file)
                    rel_name = os.path.relpath(img_path, full_path).replace("\\", "/")
                    # Key name: category + filename (e.g., "floor/grass_full_new.png")
                    key = f"{os.path.basename(sub_dir)}/{rel_name}".replace(".png", "").replace(".jpg", "").replace(".jpeg", "")
                    images.append({"key": key, "path": img_path})

    if not images:
        print("No images found to combine.")
        return

    # 2. Sort images for consistent packing
    images.sort(key=lambda x: x['key'])
    
    # 3. Simple Grid Packing
    count = len(images)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    
    # Use max dimensions of any image as grid cell size
    max_w = 0
    max_h = 0
    loaded_imgs = []
    
    print(f"Stitching {count} images into {cols}x{rows} grid...")
    
    for img_info in images:
        img = Image.open(img_info['path']).convert("RGBA")
        max_w = max(max_w, img.width)
        max_h = max(max_h, img.height)
        loaded_imgs.append((img_info['key'], img))

    atlas_w = cols * max_w
    atlas_h = rows * max_h
    
    atlas_img = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    frames = {}
    
    for idx, (key, img) in enumerate(loaded_imgs):
        c = idx % cols
        r = idx // cols
        x = c * max_w
        y = r * max_h
        
        # Paste centered in the cell if smaller
        px = x + (max_w - img.width) // 2
        py = y + (max_h - img.height) // 2
        
        atlas_img.paste(img, (px, py), img)
        
        frames[key] = {
            "frame": {"x": px, "y": py, "w": img.width, "h": img.height},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": img.width, "h": img.height},
            "sourceSize": {"w": img.width, "h": img.height}
        }

    # 4. Save
    atlas_img.save(OUTPUT_IMAGE)
    
    manifest = {
        "frames": frames,
        "meta": {
            "image": "atlas.png",
            "format": "RGBA8888",
            "size": {"w": atlas_w, "h": atlas_h},
            "scale": "1"
        }
    }
    
    with open(OUTPUT_JSON, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Atlas generated successfully: {OUTPUT_IMAGE}")

if __name__ == "__main__":
    generate_atlas()
