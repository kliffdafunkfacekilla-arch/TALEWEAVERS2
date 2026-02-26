import sys
from pathlib import Path
# Add root to sys.path to allow importing from saga_common
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum
from saga_common.models.core import ItemCategory, WealthState

# --- BASE ITEM ---
class BaseItem(BaseModel):
    id: str
    name: str
    category: ItemCategory
    weight: float
    base_value_aetherium: int

# 1. WEAPONS (Tied to the 36 Tactical Triads)
class WeaponItem(BaseItem):
    category: ItemCategory = ItemCategory.WEAPON
    damage_dice: str          # e.g., "1d8"
    damage_type: str          # "Piercing", "Blunt", "Force"
    lead_stat_required: str   # e.g., "Might", "Finesse"
    traits: List[str]         # e.g., ["Heavy", "Reach 10ft"]

# 2. ARMOR (Tied to the Stamina/Focus Holding Fees)
class ArmorItem(BaseItem):
    category: ItemCategory = ItemCategory.ARMOR
    defense_bonus: int
    stamina_lock: int = 0     # Heavy armor reduces Max Stamina
    focus_lock: int = 0       # Mystical robes reduce Max Focus

# 3. CONSUMABLES (Hedge Charms, Salves, Teas)
class ConsumableItem(BaseItem):
    category: ItemCategory = ItemCategory.CONSUMABLE
    effect_type: str          # "HEAL", "DAMAGE", "BUFF"
    effect_math: str          # e.g., "Regain 1d4 Stamina", "2d6 Fire Dmg 10ft radius"
    resist_save: Optional[str] = None # e.g., "Reflex Half"
    is_unstable: bool = False # If true, explodes on a Nat 1 throw

# 4. INFO & LORE
class InfoItem(BaseItem):
    category: ItemCategory = ItemCategory.INFO
    lore_text: str
    knowledge_triad_advantage: Optional[str] = None # e.g., "Advantage on History checks regarding the Elven Empire"

# 5. TOOLS
class ToolItem(BaseItem):
    category: ItemCategory = ItemCategory.TOOL
    skill_triad_buff: str     # e.g., "Climbing Gear: +1 to Mobility Triad"
    durability: int           # Tools break over time

# 6. QUEST ITEMS
class QuestItem(BaseItem):
    category: ItemCategory = ItemCategory.QUEST
    quest_id: str
    is_key_item: bool = True

# 7. TREASURE
class TreasureItem(BaseItem):
    category: ItemCategory = ItemCategory.TREASURE
    rarity: str               # "Common", "Rare", "Relic"
    lore_snippet: Optional[str] = None
