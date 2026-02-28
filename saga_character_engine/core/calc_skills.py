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

def calculate_skills(attributes: CoreAttributes, chosen_skills: Dict[str, str]) -> Dict:
    """
    Calculates ranks, pips, and stat bonuses based on skill selection.
    Strictly enforces:
    1. 12 skills total (1 from each triad).
    2. 6 skills must lead with Body, 6 with Mind.
    """
    triads_db = load_tactical_triads()
    
    # 1. Validation: Must have 12 skills and exactly one from each triad
    skill_lookup = {}
    selected_triads = set()
    for triad, skills in triads_db.items():
        for skill_data in skills:
            skill_lookup[skill_data["skill"]] = skill_data
            if skill_data["skill"] in chosen_skills:
                selected_triads.add(triad)
                
    # Quickplay bypass for VTT testing UI
    if len(chosen_skills) == 0:
        return {
            "skills": {},
            "stat_bonuses": {
                "might": 0, "endurance": 0, "vitality": 0, "fortitude": 0, "reflexes": 0, "finesse": 0,
                "knowledge": 0, "logic": 0, "charm": 0, "willpower": 0, "awareness": 0, "intuition": 0
            }
        }
                
                
    if len(chosen_skills) != 12:
         # Note: We return error as string or raise for the API to handle
         raise ValueError(f"Character must select exactly 12 skills. Selected: {len(chosen_skills)}")

    if len(selected_triads) != 12:
         raise ValueError(f"Character must select exactly 1 skill from each of the 12 Triads. Triads selected: {len(selected_triads)}.")

    # 2. Validation: 6 Body / 6 Mind split
    leads = [pref.lower() for pref in chosen_skills.values()]
    body_count = leads.count("body")
    mind_count = leads.count("mind")
    
    if body_count != 6 or mind_count != 6:
        raise ValueError(f"Skill Leads must be split exactly 6-Body and 6-Mind. Current: {body_count} Body, {mind_count} Mind.")

    # 3. Calculation
    compiled_skills = {}
    skill_stat_bonuses = {
        "might": 0, "endurance": 0, "vitality": 0, "fortitude": 0, "reflexes": 0, "finesse": 0,
        "knowledge": 0, "logic": 0, "charm": 0, "willpower": 0, "awareness": 0, "intuition": 0
    }
    
    # Define the sets for sector matching
    BODY_STATS = {"might", "endurance", "vitality", "fortitude", "reflexes", "finesse"}
    MIND_STATS = {"knowledge", "logic", "charm", "willpower", "awareness", "intuition"}

    for skill_name, lead_preference in chosen_skills.items():
        if skill_name not in skill_lookup:
            continue
            
        data = skill_lookup[skill_name]
        # stat_pair usually looks like "Might + Knowledge"
        parts = [p.strip().lower() for p in data["stat_pair"].split("+")]
        if len(parts) == 2:
            # Normalize stat names (reflex -> reflexes)
            parts = ["reflexes" if p == "reflex" else p for p in parts]
            
            # Determine which is Body and which is Mind based on Sectors
            body_stat = next((p for p in parts if p in BODY_STATS), parts[0])
            mind_stat = next((p for p in parts if p in MIND_STATS), parts[1])
            
            # Application: In TALEWEAVERS, each skill gives exactly +1 point total.
            # We apply it strictly to the chosen LEAD stat (Body or Mind).
            lead_stat = body_stat if lead_preference.lower() == "body" else mind_stat
            
            if lead_stat in skill_stat_bonuses: 
                skill_stat_bonuses[lead_stat] += 1
            
            # Get values for rank/pip calculation
            lead_val = getattr(attributes, lead_stat, 10)
            
            # Math: Rank = Lead / 5, Pip = Lead % 5
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
