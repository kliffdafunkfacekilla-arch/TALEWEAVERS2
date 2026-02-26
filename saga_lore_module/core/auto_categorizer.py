import re
from .schemas import LoreCategory

def categorize_text(text: str) -> str:
    """
    Keyword-based heuristic categorization for un-tagged documents.
    """
    text_lower = text.lower()
    
    # Heuristics based on common fantasy tropes and game requirements
    heuristics = {
        LoreCategory.POLITICAL_FACTION: ["faction", "empire", "kingdom", "alliance", "treaty", "senate", "rebel", "council", "territory", "capital", "noble"],
        LoreCategory.PLANT: ["flora", "leaf", "root", "bloom", "grows", "herb", "shrub"],
        LoreCategory.ANIMAL: ["beast", "fauna", "creature", "habitat", "fur", "scales", "migration"],
        LoreCategory.RESOURCE: ["ore", "mine", "aetherium", "supply", "trade", "harvest", "scarcity"],
        LoreCategory.BIOME: ["climate", "terrain", "swamp", "mountain", "desert", "tundra", "ecosystem"],
        LoreCategory.TECH: ["forge", "mechanism", "gears", "automation", "steam", "alchemy", "invention"],
        LoreCategory.MAGIC: ["spell", "ritual", "enchantment", "mana", "leyline", "wizard", "sorcerer"],
        LoreCategory.ITEM: ["artifact", "relic", "equipment", "weapon", "shield", "trinket", "consumable"],
        LoreCategory.PERSON: ["npc", "hero", "villain", "biography", "descendant", "legacy", "ruler"],
        LoreCategory.LOCAL_FACTION: ["guild", "cult", "coven", "militia", "neighborhood", "gang", "tribe"],
        LoreCategory.HISTORY: ["era", "ancient", "war", "chronicle", "legacy", "ruins", "archeology"],
        LoreCategory.CULTURE: ["tradition", "language", "dialect", "custom", "etiquette", "festival", "folklore"]
    }
    # Extract all whole words from the text to prevent substring matching 
    # (e.g. 'fur' in 'further' triggering ANIMAL, or 'ore' in 'forest' triggering RESOURCE)
    words_in_text = set(re.findall(r'\b\w+\b', text_lower))
    
    # Count matches for each category
    counts = {}
    for category, keywords in heuristics.items():
        count = sum(1 for word in keywords if word in words_in_text)
        if count > 0:
            counts[category] = count
            
    if not counts:
        return LoreCategory.LORE
        
    # Return the category with the most matches
    return max(counts, key=counts.get)
