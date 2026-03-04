from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum

# --- ENUMS ---
class ItemCategory(str, Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    TOOL = "TOOL"
    CONSUMABLE = "CONSUMABLE"
    QUEST = "QUEST"
    TREASURE = "TREASURE"
    INFO = "INFO"

# --- CORE CHARACTER SCHEMAS ---
class PipBank(BaseModel):
    stars: int = 0
    scars: int = 0
    survivors: int = 0

class CoreAttributes(BaseModel):
    # Sector I: Physical
    might: int = 0
    endurance: int = 0
    vitality: int = 0
    fortitude: int = 0
    reflexes: int = 0
    finesse: int = 0
    
    # Sector II: Mental
    knowledge: int = 0
    logic: int = 0
    charm: int = 0
    willpower: int = 0
    awareness: int = 0
    intuition: int = 0

class DerivedVitals(BaseModel):
    max_hp: int
    max_stamina: int
    max_composure: int
    max_focus: int
    
    # Dual-Track Injury Slots
    body_injuries: List[str] = []
    mind_injuries: List[str] = []

# --- ITEM & ECONOMY SCHEMAS ---
class WealthState(BaseModel):
    aetherium_coins: int = 0
    d_dust_grams: float = 0.0
    current_exchange_rate: float = 1.0

class SpriteMetadata(BaseModel):
    sheet_url: str            # e.g., "/assets/icons/weapons1.png"
    x: int = 0                # Top-left X in pixels
    y: int = 0                # Top-left Y in pixels
    w: int = 32               # Width in pixels
    h: int = 32               # Height in pixels

# --- CLASH & COMBAT SCHEMAS ---
class CombatantState(BaseModel):
    name: str
    avatar_sprite: Optional[SpriteMetadata] = None
    current_hp: int = 10
    attack_or_defense_pool: int = 0
    skill_rank: int = 0
    stat_mod: int = 0
    weapon_damage_dice: Optional[str] = None
    stamina_burned: int = 0
    focus_burned: int = 0
