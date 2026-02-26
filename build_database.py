import csv
import json
import os

RAW_DATA_DIR = "raw_data"
OUTPUT_FILE = "data/Evolution_Matrix.json"

def clean_stat_name(stat_str):
    """Maps CSV stat names to our Pydantic schema names."""
    mapping = {
        "Might": "might", "Endurance": "endurance", "Endure": "endurance",
        "Vitality": "vitality", "Fortitude": "fortitude", 
        "Reflex": "reflexes", "Reflexes": "reflexes", "Finesse": "finesse",
        "Knowledge": "knowledge", "Logic": "logic", "Charm": "charm", 
        "Will": "willpower", "Willpower": "willpower", 
        "Awareness": "awareness", "Intuition": "intuition", "None": None
    }
    return mapping.get(stat_str.strip(), stat_str.strip().lower())

def build_matrix():
    print("Forging Evolution Matrix from CSVs...")
    evolution_db = []
    
    # We will look for all species files
    species_list = ["Plant", "Avian", "Reptile", "Insect", "Aquatic", "Mammal"]
    
    for species in species_list:
        body_csv = os.path.join(RAW_DATA_DIR, f"{species}.csv")
        skills_csv = os.path.join(RAW_DATA_DIR, f"{species}_Skills.csv")
        
        # Dictionary to hold skills temporarily: { "Hooked Beak": [{"name": "Tear Flesh", ...}] }
        skills_map = {}
        
        # 1. Parse the Skills CSV
        if os.path.exists(skills_csv):
            with open(skills_csv, mode='r', encoding='windows-1252', errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    body_part = row.get("Body Part", "").strip()
                    if body_part:
                        if body_part not in skills_map:
                            skills_map[body_part] = []
                        skills_map[body_part].append({
                            "name": row.get("Skill Name", "Unknown Skill"),
                            "type": row.get("Type", "Passive"),
                            "effect": row.get("Effect Description", "")
                        })

        # 2. Parse the Body/Evolution CSV
        if os.path.exists(body_csv):
            with open(body_csv, mode='r', encoding='windows-1252', errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    part_name = row.get("Body Part", "").strip()
                    if not part_name or part_name == "None":
                        continue
                        
                    # Build the stat modifiers (We assign +1 to Stat 1, and +1 to Stat 2 for simplicity based on your matrix logic)
                    stat_mods = {}
                    s1 = clean_stat_name(row.get("Stat 1", ""))
                    s2 = clean_stat_name(row.get("Stat 2", ""))
                    if s1: stat_mods[s1] = stat_mods.get(s1, 0) + 1
                    if s2: stat_mods[s2] = stat_mods.get(s2, 0) + 1

                    # Attach the parsed skills
                    passives = skills_map.get(part_name, [])
                    
                    # Also grab the raw "Mechanic / Trait" from the main CSV just in case
                    raw_mechanic = row.get("Mechanic / Trait", "")
                    if raw_mechanic and not passives:
                        passives.append({
                            "name": part_name + " Trait",
                            "type": "Biological Trait",
                            "effect": raw_mechanic
                        })

                    evolution_db.append({
                        "name": part_name,
                        "species": species,
                        "stats": stat_mods,
                        "passives": passives
                    })

    # Add the "Standard" fallback so players can be normal
    evolution_db.append({"name": "Standard", "stats": {}, "passives": []})

    # Save to the Master JSON!
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(evolution_db, f, indent=4)
    
    print(f"Matrix Forged! Extracted {len(evolution_db)} biological traits into {OUTPUT_FILE}.")

if __name__ == "__main__":
    build_matrix()
