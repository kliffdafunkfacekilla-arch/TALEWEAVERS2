import re
from .lore_schemas import LoreCategory

def categorize_text(text: str, filepath: str = "") -> str:
    """
    Categorizes based on folder path first, then falls back to term-frequency heuristics.
    """
    text_lower = text.lower()
    path_lower = filepath.lower()

    # --- TIER 1: FOLDER PATH CHEAT CODES ---
    # If the file is inside a specific folder, trust the user's organization 100%
    if any(w in path_lower for w in ["faction", "organization", "guild", "cult"]): return LoreCategory.POLITICAL_FACTION
    if any(w in path_lower for w in ["npc", "character", "people"]): return LoreCategory.PERSON
    if any(w in path_lower for w in ["item", "equipment", "loot", "relic"]): return LoreCategory.ITEM
    if any(w in path_lower for w in ["location", "city", "region", "biome"]): return LoreCategory.BIOME
    if any(w in path_lower for w in ["flora", "plant", "herb"]): return LoreCategory.PLANT
    if any(w in path_lower for w in ["fauna", "fuana", "beast", "monster"]): return LoreCategory.ANIMAL
    if any(w in path_lower for w in ["resource", "material", "ore", "mineral"]): return LoreCategory.RESOURCE
    if any(w in path_lower for w in ["history", "lore", "myth"]): return LoreCategory.HISTORY

    # --- TIER 2: TERM FREQUENCY HEURISTICS ---
    heuristics = {
        LoreCategory.POLITICAL_FACTION: ["faction", "empire", "kingdom", "alliance", "treaty", "senate", "rebel", "council", "territory", "capital", "noble"],
        LoreCategory.PLANT: ["flora", "leaf", "root", "bloom", "grows", "herb", "shrub", "moss"],
        LoreCategory.ANIMAL: ["beast", "fauna", "creature", "habitat", "fur", "scales", "migration", "predator"],
        LoreCategory.RESOURCE: ["ore", "mine", "aetherium", "supply", "trade", "harvest", "scarcity", "metal"],
        LoreCategory.BIOME: ["climate", "terrain", "swamp", "mountain", "desert", "tundra", "ecosystem"],
        LoreCategory.TECH: ["forge", "mechanism", "gears", "automation", "steam", "alchemy", "invention"],
        LoreCategory.MAGIC: ["spell", "ritual", "enchantment", "mana", "leyline", "wizard", "sorcerer"],
        LoreCategory.ITEM: ["artifact", "relic", "equipment", "weapon", "shield", "trinket", "consumable"],
        LoreCategory.PERSON: ["npc", "hero", "villain", "biography", "descendant", "legacy", "ruler"],
        LoreCategory.LOCAL_FACTION: ["guild", "cult", "coven", "militia", "neighborhood", "gang", "tribe"],
        LoreCategory.HISTORY: ["era", "ancient", "war", "chronicle", "legacy", "ruins", "archeology"],
        LoreCategory.CULTURE: ["tradition", "language", "dialect", "custom", "etiquette", "festival", "folklore"]
    }
    
    counts = {}
    for category, keywords in heuristics.items():
        score = 0
        for word in keywords:
            # Count EVERY occurrence of the word in the text, not just if it exists
            score += len(re.findall(rf'\b{word}\b', text_lower))
        
        if score > 0:
            counts[category] = score
            
    if not counts:
        return LoreCategory.LORE
        
    # Return the category with the absolute highest frequency of matching words
    return max(counts, key=counts.get)
