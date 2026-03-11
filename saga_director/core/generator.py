import random
import uuid
from .encounter_schemas import (
    EncounterRequest, EncounterResponse, EncounterCategory, 
    DiscoveryEncounter, DilemmaEncounter, DilemmaOption, SpatialData
)
from .gen_social import generate_social_denizen
from .gen_hazard import generate_tactical_hazard
from .gen_combat import generate_hostile_threat

def generate_spatial(radius: float = 1.0) -> SpatialData:
    """Fallback generator for offsets from hex center."""
    return SpatialData(
        x_offset=random.uniform(-10.0, 10.0),
        y_offset=random.uniform(-10.0, 10.0),
        footprint_radius=radius
    )

def generate_encounter(request: EncounterRequest) -> EncounterResponse:
    # 1. Determine Type
    enc_type = request.forced_type
    if not enc_type:
        types = list(EncounterCategory)
        weights = [25, 20, 20, 15, 10, 10] # Combat, Social, Hazard, Puzzle, Dilemma, Discovery
        if request.biome == "Dungeon":
            weights = [40, 5, 30, 20, 0, 5]
        elif request.biome == "City":
             weights = [10, 60, 5, 10, 10, 5]
        
        enc_type = random.choices(types, weights=weights, k=1)[0]

    # 2. Build Encounter Data based on type
    data = None
    if enc_type == EncounterCategory.SOCIAL:
        data = generate_social_denizen(request.faction_territory or "Neutral", request.threat_level)
    elif enc_type == EncounterCategory.HAZARD:
        data = generate_tactical_hazard(request.threat_level)
    elif enc_type == EncounterCategory.COMBAT:
        data = generate_hostile_threat(request.threat_level, request.seed_prompt, request.biome or "Forest")
    elif enc_type == EncounterCategory.PUZZLE:
        data = _gen_puzzle_fallback(request)
    elif enc_type == EncounterCategory.DILEMMA:
        data = _gen_dilemma_fallback(request)
    else:
        data = _gen_discovery_fallback(request)

    return EncounterResponse(
        encounter_id=f"ENC_{uuid.uuid4().hex[:8].upper()}_{enc_type.value}",
        data=data
    )

def _gen_puzzle_fallback(request: EncounterRequest) -> DiscoveryEncounter:
    return DiscoveryEncounter(
        title="Strange Mechanism",
        narrative_prompt="A brass device hums with a low frequency. It requires a Logic + Knowledge check to decipher.",
        loot_tags=["Old-Tech"],
        interaction_required=True,
        spatial=generate_spatial(radius=2.0)
    )

def _gen_dilemma_fallback(request: EncounterRequest) -> DilemmaEncounter:
    return DilemmaEncounter(
        title="The Choice",
        narrative_prompt="A merchant's wagon is suspended over a cliff. You can save the merchant or the cargo.",
        options=[
            DilemmaOption(label="Save Merchant", consequence_mechanic="LOSE_STAMINA_2", consequence_narrative="The merchant lives and offers a future discount."),
            DilemmaOption(label="Save Cargo", consequence_mechanic="GAIN_AETHERIUM_50", consequence_narrative="The merchant falls, but you secure the coins.")
        ]
    )

def _gen_discovery_fallback(request: EncounterRequest) -> DiscoveryEncounter:
    return DiscoveryEncounter(
        title="Hidden Cache",
        narrative_prompt="You find a crate marked with an ancient seal.",
        loot_tags=["Scrap", "Artifact"],
        interaction_required=True,
        spatial=generate_spatial(radius=1.5)
    )
