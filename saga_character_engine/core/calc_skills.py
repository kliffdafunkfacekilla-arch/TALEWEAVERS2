import json
from pathlib import Path
from typing import Dict, List, Optional
from .schemas import CoreAttributes

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

def load_tactical_triads() -> Dict[str, List[Dict[str, str]]]:
    """Loads the 36 Tactical Skills grouped by their 12 Triads."""
    triads_path = DATA_DIR / "tactical_triads.json"
    if triads_path.exists():
        with open(triads_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"[WARNING] Could not find {triads_path}. Using empty tactical triads.")
    return {}

def calculate_skills(
    attributes: CoreAttributes, 
    chosen_skills: Dict[str, str]
) -> Dict[str, Dict[str, int]]:
    """
    Calculates the rank and pips for each chosen skill.
    In TALEWEAVERS, a skill is linked to a Body stat and a Mind stat. 
    The player chooses which they "Lead" with, and the other becomes the "Trail".
    For now, we simply calculate Rank = (Lead Stat + Trail Stat) // 2 as an example algorithm, 
    or whatever specific pip translation the system needs. If there is a strict math 
    definition, we can adjust here. Right now we map the base sum.
    
    Format of chosen_skills: {"Aggressive": "Body", "Command": "Mind"}
    """
    triads_db = load_tactical_triads()
    
    # Flatten the DB into a skill name lookup
    skill_lookup = {}
    for triad, skills in triads_db.items():
        for skill_data in skills:
            skill_lookup[skill_data["skill"]] = skill_data
            
    compiled_skills = {}
    
    for skill_name, lead_preference in chosen_skills.items():
        if skill_name not in skill_lookup:
            continue
            
        data = skill_lookup[skill_name]
        # stat_pair usually looks like "Might + Knowledge"
        parts = [p.strip().lower() for p in data["stat_pair"].split("+")]
        if len(parts) == 2:
            body_stat = parts[0]
            mind_stat = parts[1]
            
            body_val = getattr(attributes, body_stat, 0)
            mind_val = getattr(attributes, mind_stat, 0)
            
            lead_val = body_val if lead_preference.lower() == "body" else mind_val
            trail_val = mind_val if lead_preference.lower() == "body" else body_val
            
            # Placeholder math for Ranks and Pips. For example, Rank = Lead / 2.
            rank = (lead_val + trail_val) // 4
            pips = (lead_val + trail_val) % 4
            
            compiled_skills[skill_name] = {
                "rank": rank,
                "pips": pips
            }
            
    return compiled_skills
