import json
from pathlib import Path
from typing import List, Dict, Set
from .schemas import CoreAttributes

# Safely point to the master data folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def load_tactical_triads() -> Dict[str, List[Dict]]:
    """Loads the real tactical_triads.json from the master database."""
    triads_path = DATA_DIR / "tactical_triads.json"
    if triads_path.exists():
        with open(triads_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def calculate_skills(attributes: CoreAttributes, chosen_skills: Dict[str, Dict[str, int]]) -> Dict:
    """
    Calculates ranks, pips, and stat bonuses based on skill selection.
    Strictly enforces:
    1. 12 skills total (1 from each triad).
    2. Uses internal stat pairs to identify lead stat dynamically.
    """
    triads_db = load_tactical_triads()
    
    # Quickplay bypass for VTT testing UI
    if len(chosen_skills) == 0:
        return {
            "skills": {},
            "stat_bonuses": {
                "might": 0, "endurance": 0, "vitality": 0, "fortitude": 0, "reflexes": 0, "finesse": 0,
                "knowledge": 0, "logic": 0, "charm": 0, "willpower": 0, "awareness": 0, "intuition": 0
            }
        }

    skill_lookup = {}
    selected_triads = set()
    for triad, skills in triads_db.items():
        for skill_data in skills:
            skill_lookup[skill_data["skill"]] = skill_data
            if skill_data["skill"] in chosen_skills:
                selected_triads.add(triad)
                
    if len(chosen_skills) != 12:
         raise ValueError(f"Character must select exactly 12 skills. Selected: {len(chosen_skills)}")

    if len(selected_triads) != 12:
         raise ValueError(f"Character must select exactly 1 skill from each of the 12 Triads. Triads selected: {len(selected_triads)}.")

    compiled_skills = {}
    skill_stat_bonuses = {
        "might": 0, "endurance": 0, "vitality": 0, "fortitude": 0, "reflexes": 0, "finesse": 0,
        "knowledge": 0, "logic": 0, "charm": 0, "willpower": 0, "awareness": 0, "intuition": 0
    }
    
    BODY_STATS = {"might", "endurance", "vitality", "fortitude", "reflexes", "finesse"}
    MIND_STATS = {"knowledge", "logic", "charm", "willpower", "awareness", "intuition"}

    for skill_name, skill_val_dict in chosen_skills.items():
        if skill_name not in skill_lookup:
            continue
            
        data = skill_lookup[skill_name]
        parts = [p.strip().lower() for p in data["stat_pair"].split("+")]
        if len(parts) == 2:
            parts = ["reflexes" if p == "reflex" else p for p in parts]
            body_stat = next((p for p in parts if p in BODY_STATS), parts[0])
            mind_stat = next((p for p in parts if p in MIND_STATS), parts[1])
            
            # The user's provided input specifies the current rank/pip from UI logic,
            # but we need to derive the lead stat accurately. 
            body_val = getattr(attributes, body_stat, 10)
            mind_val = getattr(attributes, mind_stat, 10)

            # Use the user's provided lead preference from the character creation UI
            lead_preference = skill_val_dict.get("lead", "Body")
            lead_stat = body_stat if lead_preference.lower() == "body" else mind_stat

            if lead_stat in skill_stat_bonuses: 
                skill_stat_bonuses[lead_stat] += 1
            
            lead_val = getattr(attributes, lead_stat, 10)
            
            rank = lead_val // 5
            pips = lead_val % 5
            
            compiled_skills[skill_name] = {
                "rank": rank,
                "pips": pips,
                "lead": lead_preference
            }

    return {
        "skills": compiled_skills,
        "stat_bonuses": skill_stat_bonuses
    }
