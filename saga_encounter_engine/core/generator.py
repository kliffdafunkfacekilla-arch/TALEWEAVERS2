import json
import random
import uuid
from typing import Optional
from .schemas import (
    EncounterRequest, EncounterResponse, EncounterCategory, 
    SocialEncounter, SocialNPC, HazardEncounter, 
    PuzzleEncounter, DiscoveryEncounter, DilemmaEncounter, DilemmaOption,
    CombatEncounter, Combatant
)

DATA_PATH = "data/"

def load_data(filename: str):
    with open(f"{DATA_PATH}{filename}", "r") as f:
        return json.load(f)

def generate_encounter(request: EncounterRequest) -> EncounterResponse:
    # 1. Determine Type
    enc_type = request.forced_type
    if not enc_type:
        # Weighted roll based on threat level and biome (simplified for now)
        types = list(EncounterCategory)
        weights = [20, 20, 20, 15, 15, 10] # Default
        if request.biome == "Dungeon":
            weights = [40, 5, 30, 20, 5, 0]
        elif request.biome == "City":
             weights = [5, 60, 5, 10, 10, 10]
        
        enc_type = random.choices(types, weights=weights, k=1)[0]

    # 2. Build Encounter Data based on type
    data = None
    if enc_type == EncounterCategory.SOCIAL:
        data = _gen_social(request)
    elif enc_type == EncounterCategory.HAZARD:
        data = _gen_hazard(request)
    elif enc_type == EncounterCategory.PUZZLE:
        data = _gen_puzzle(request)
    elif enc_type == EncounterCategory.DILEMMA:
        data = _gen_dilemma(request)
    elif enc_type == EncounterCategory.DISCOVERY:
        data = _gen_discovery(request)
    else:
        data = _gen_combat(request)

    return EncounterResponse(
        encounter_id=f"ENC_{uuid.uuid4().hex[:8].upper()}_{enc_type}",
        data=data
    )

def _gen_social(request: EncounterRequest) -> SocialEncounter:
    archetypes = load_data("npc_archetypes.json")
    arc_name = random.choice(list(archetypes.keys()))
    arc = archetypes[arc_name]
    
    npc = SocialNPC(
        name=f"{arc_name} of {request.faction_territory or 'the Wastes'}",
        species="Human", # Default
        faction=request.faction_territory or "Independent",
        disposition=arc["disposition"],
        motives=arc["motives"],
        composure_pool=arc["base_stats"]["willpower"] + arc["base_stats"]["logic"],
        willpower=arc["base_stats"]["willpower"],
        logic=arc["base_stats"]["logic"],
        awareness=arc["base_stats"]["awareness"],
        trade_inventory=["Ration", "D-Dust"] if arc["inventory_type"] == "General" else []
    )
    
    return SocialEncounter(
        title=f"A meeting with a {arc_name}",
        narrative_prompt=f"You encounter a {arc_name} who looks {npc.disposition.lower()}.",
        npcs=[npc]
    )

def _gen_hazard(request: EncounterRequest) -> HazardEncounter:
    templates = load_data("hazard_templates.json")
    temp_name = random.choice(list(templates.keys()))
    temp = templates[temp_name]
    
    return HazardEncounter(
        title=temp["title"],
        narrative_prompt=temp["narrative"],
        detection_check={"triad": temp["detection"]["triad"], "dc": temp["detection"]["dc_base"] + request.threat_level},
        disarm_check={"triad": temp["disarm"]["triad"], "dc": temp["disarm"]["dc_base"] + request.threat_level} if temp["disarm"] else None,
        trigger_effect=temp["effect"]
    )

def _gen_puzzle(request: EncounterRequest) -> PuzzleEncounter:
    logic = load_data("puzzle_logic.json")
    puz_name = random.choice(list(logic.keys()))
    puz = logic[puz_name]
    
    return PuzzleEncounter(
        title=puz["title"],
        narrative_prompt=puz["narrative"],
        logic_gate=puz["logic_gate"],
        required_triad=puz["required_triad"],
        dc=puz["dc_base"] + request.threat_level,
        failure_cost=puz["failure_cost"]
    )

def _gen_dilemma(request: EncounterRequest) -> DilemmaEncounter:
    return DilemmaEncounter(
        title="Tactical Dilemma",
        narrative_prompt="You find a wounded scout from a rival faction. They carry vital intelligence but are dying.",
        options=[
            DilemmaOption(label="Save the Scout", consequence_mechanic="LOSE_STAMINA_2", consequence_narrative="You gain their trust but feel the strain of the rescue."),
            DilemmaOption(label="Take the intel and leave", consequence_mechanic="REVEAL_HEX_TRAP", consequence_narrative="You know the dangers ahead, but the scout perishes.")
        ]
    )

def _gen_combat(request: EncounterRequest) -> CombatEncounter:
    return CombatEncounter(
        title="Hostile Ambush",
        narrative_prompt="Creatures lunge from the shadows!",
        enemies=[
            Combatant(name="Scavenger", rank="Mook", hp=10, stamina=5, traits=["Fast"], weapons=["Rust Dagger"], armor=1)
        ],
        terrain_difficulty=3,
        escape_dc=12
    )

def _gen_discovery(request: EncounterRequest) -> DiscoveryEncounter:
    return DiscoveryEncounter(
        title="Ancient Cache",
        narrative_prompt="Under a pile of rubble, you spot the corner of a metal crate.",
        loot_tags=["Old-Tech", "Aetherium"],
        interaction_required=True
    )
