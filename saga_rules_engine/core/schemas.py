import sys
from pathlib import Path
# Add root to sys.path to allow importing from saga_common
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from saga_common.models.core import CoreAttributes, DerivedVitals, PipBank, ItemCategory, WealthState, SpriteMetadata

class RollState(BaseModel):
    is_advantage: bool = False
    is_disadvantage: bool = False
    focus_spent: int = 0       # Players can burn Focus to add dice/bonuses

class SkillCheckRequest(BaseModel):
    character_id: str
    triad_name: str            # e.g., "Awareness + Intuition"
    lead_stat_value: int
    trail_stat_value: int
    skill_rank: int            # 0 to 5
    target_dc: int
    roll_state: RollState
    is_life_or_death: bool = False # Director toggles this to allow "Survivor" pips

class SkillCheckResult(BaseModel):
    roll_total: int
    raw_die_face: int          # Needed to check for Nat 1s and Nat 20s
    is_success: bool
    margin: int
    scars_and_stars_trigger: Optional[str] = None # "STAR", "SCAR", "SURVIVOR", or None

# --- BASE ITEM ---
class BaseItem(BaseModel):
    id: str
    name: str
    category: ItemCategory
    weight: float
    base_value_aetherium: int
    tags: List[str] = []
    sprite: Optional[SpriteMetadata] = None # Added for visual rendering

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

class CompositeLayer(BaseModel):
    sheet_url: str
    x: int
    y: int
    w: int
    h: int
    tint: Optional[int] = None

class CompositeSprite(BaseModel):
    layers: List[CompositeLayer]

class BiologicalEvolutions(BaseModel):
    species_base: str    # e.g., "PLANT", "AVIAN"
    size_slot: str = "Standard"
    ancestry_slot: str = "Standard"
    head_slot: str = "Standard"
    body_slot: str = "Standard"
    arms_slot: str = "Standard"
    legs_slot: str = "Standard"
    skin_slot: str = "Standard"
    special_slot: str = "Standard"

class CharacterBuildRequest(BaseModel):
    name: str = "Subject 001"
    base_attributes: Optional[CoreAttributes] = None
    evolutions: BiologicalEvolutions
    background_training: str = "None"
    tactical_skills: Dict[str, Dict[str, str]] = {} # e.g. {"Aggressive": {"lead": "Body"}}
    selected_powers: List[Dict[str, str]] = [] # Expecting full power obj or strings
    equipped_loadout: Dict[str, str] = {}
    pip_bank: PipBank = Field(default_factory=PipBank)
    composite_sprite: Optional[CompositeSprite] = None

class CompiledSkill(BaseModel):
    rank: int
    pips: int
    lead: str

class CompiledCharacterSheet(BaseModel):
    name: str
    attributes: CoreAttributes
    vitals: DerivedVitals
    evolutions: BiologicalEvolutions
    passives: List[Dict[str, str]] = []
    tactical_skills: Dict[str, CompiledSkill] = {} # e.g. {"Aggressive": {"rank": 1, "pips": 0, "lead": "Body"}}
    powers: List[Dict[str, str]] = []
    loadout: Dict[str, str] = {}
    holding_fees: Dict[str, int] = {"stamina": 0, "focus": 0}
    pip_bank: PipBank = Field(default_factory=PipBank)
    composite_sprite: Optional[CompositeSprite] = None
