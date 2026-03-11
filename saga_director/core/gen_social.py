import random
import os
import json
from .encounter_schemas import SocialEncounter, SocialNPC, SpatialData

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def load_archetypes():
    with open(os.path.join(DATA_DIR, "npc_archetypes.json"), "r") as f:
        return json.load(f)

def generate_social_denizen(faction: str, threat_level: int) -> SocialEncounter:
    archetypes = load_archetypes()
    arc_name = random.choice(list(archetypes.keys()))
    arc = archetypes[arc_name]
    
    npc = SocialNPC(
        name=f"{arc_name} of {faction}",
        species="Human",
        faction=faction,
        disposition=arc["disposition"],
        motives=random.sample(arc["motives"], min(2, len(arc["motives"]))),
        composure_pool=arc["base_stats"]["willpower"] + arc["base_stats"]["logic"] + (threat_level * 2),
        willpower=arc["base_stats"]["willpower"] + threat_level,
        logic=arc["base_stats"]["logic"] + threat_level,
        awareness=arc["base_stats"]["awareness"] + threat_level,
        trade_inventory=["Ration", "D-Dust"] if arc["inventory_type"] == "General" else ["Scrap Metal"],
        spatial=SpatialData(
            x_offset=random.uniform(-8.0, 8.0),
            y_offset=random.uniform(-8.0, 8.0),
            footprint_radius=1.2
        )
    )
    
    return SocialEncounter(
        title=f"The {arc_name}",
        narrative_prompt=f"A figure wrapped in travel-worn cloaks approaches. It is a {arc_name} from {faction}.",
        npcs=[npc]
    )
