import json
import os

species_list = ["AQUATIC", "AVIAN", "INSECT", "MAMMAL", "PLANT", "REPTILE"]

shared_traits = {
    "head_slot": [
        {"name": "Reinforced Skull", "stats": {"fortitude": 1}, "effect": "Passive: Advantage on checks against being Stunned or Dazed."},
        {"name": "Predator Senses", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Awareness checks to locate hidden enemies."},
        {"name": "Expanded Cranium", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack."},
        {"name": "Resonance Chamber", "stats": {"charm": 1}, "effect": "Passive: Allies within 30ft hear you perfectly. Gain Advantage on Social Intimidation/Persuasion."}
    ],
    "body_slot": [
        {"name": "Bone Plating", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense."},
        {"name": "Flexible Spine", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks."},
        {"name": "Aetheric Conduit", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus."},
        {"name": "Pheromone Glands", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ],
    "arms_slot": [
        {"name": "Crushing Limbs", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Concealed Blades", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Channeled Palms", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away."},
        {"name": "Shielding Forearms", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ],
    "legs_slot": [
        {"name": "Pillar Stance", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Spring Tendons", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Levitation Nodes", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Vanguard Stride", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ],
    "skin_slot": [
        {"name": "Calloused Hide", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Chroma-Skin", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Runic Scarring", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Soothing Aura", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ],
    "special_slot": [
        {"name": "Adrenaline Surge", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Shadow Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Mind Blank", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower Defense Check."},
        {"name": "Rallying Cry", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ]
}

unique_traits = {
    "AQUATIC": {
        "head_slot": {"name": "Sonar Dome", "stats": {"awareness": 1}, "effect": "Passive: Blindsight 30ft underwater or in total darkness."},
        "body_slot": {"name": "Blubber Layer", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Cold. Ignore freezing difficult terrain."},
        "arms_slot": {"name": "Tentacle Grips", "stats": {"might": 1}, "effect": "Passive: Advantage on Grapple checks."},
        "legs_slot": {"name": "Jet Siphon", "stats": {"reflexes": 1}, "effect": "Action: Once per encounter, dash 30ft in a straight line underwater."},
        "skin_slot": {"name": "Mucus Coat", "stats": {"vitality": 1}, "effect": "Passive: Advantage on checks to escape grapples or bindings."},
        "special_slot": {"name": "Ink Sac", "stats": {"finesse": 1}, "effect": "Action: Once per cycle, create a 15ft radius cloud of blinding ink/smoke."}
    },
    "AVIAN": {
        "head_slot": {"name": "Magnifying Lens", "stats": {"awareness": 1}, "effect": "Passive: No disadvantage on ranged attacks at long range. Ignore partial cover."},
        "body_slot": {"name": "Hollow Bones", "stats": {"finesse": 1}, "effect": "Passive: Take zero falling damage. Base jump distance doubled."},
        "arms_slot": {"name": "Winged Appendages", "stats": {"reflexes": 1}, "effect": "Passive: Gain a Glide speed equal to your walking speed."},
        "legs_slot": {"name": "Grasping Talons", "stats": {"might": 1}, "effect": "Passive: Can pick up and carry objects/enemies of your size class while airborne."},
        "skin_slot": {"name": "Insulating Down", "stats": {"vitality": 1}, "effect": "Passive: Resistance to Cold and Lightning damage."},
        "special_slot": {"name": "Syrinx Box", "stats": {"charm": 1}, "effect": "Action: Perfectly mimic any voice or sound you have heard."}
    },
    "INSECT": {
        "head_slot": {"name": "Compound Eyes", "stats": {"intuition": 1}, "effect": "Passive: Cannot be flanked. Advantage on Initiative rolls."},
        "body_slot": {"name": "Chitin Carapace", "stats": {"fortitude": 1}, "effect": "Passive: +3 Natural Defense, but cannot wear heavy armor gear."},
        "arms_slot": {"name": "Mantis Scythes", "stats": {"finesse": 1}, "effect": "Passive: Unarmed attacks deal 1d6 Piercing. Critical Hit on 19-20."},
        "legs_slot": {"name": "Wall-Crawler", "stats": {"reflexes": 1}, "effect": "Passive: Gain a climbing speed equal to walking speed. Can climb on ceilings."},
        "skin_slot": {"name": "Warning Colors", "stats": {"charm": 1}, "effect": "Passive: Advantage on Intimidation checks against wild beasts and creatures."},
        "special_slot": {"name": "Pheromone Cloud", "stats": {"logic": 1}, "effect": "Action: Once per encounter, force enemies within 10ft to have disadvantage on all attacks for 1 turn."}
    },
    "MAMMAL": {
        "head_slot": {"name": "Keen Senses", "stats": {"awareness": 1}, "effect": "Passive: Advantage on tracking via scent or hearing."},
        "body_slot": {"name": "Redundant Organs", "stats": {"vitality": 1}, "effect": "Passive: When reduced to 0 HP, drop to 1 HP instead once per cycle."},
        "arms_slot": {"name": "Opposable Thumbs", "stats": {"logic": 1}, "effect": "Passive: Advantage on using complex tools or repairing tech elements."},
        "legs_slot": {"name": "Beastial Sprint", "stats": {"might": 1}, "effect": "Action: Once per encounter, drop on all fours and move up to 3x your speed."},
        "skin_slot": {"name": "Thick Fur", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Bludgeoning damage in close-quarters."},
        "special_slot": {"name": "Primal Roar", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, grant yourself and allies Advantage on their next damage roll."}
    },
    "PLANT": {
        "head_slot": {"name": "Photosensors", "stats": {"knowledge": 1}, "effect": "Passive: Regenerate 1 HP per hour while standing in direct sunlight."},
        "body_slot": {"name": "Iron-Wood Core", "stats": {"fortitude": 1}, "effect": "Passive: Resistance to Piercing damage. Vulnerable to Fire."},
        "arms_slot": {"name": "Vine Whips", "stats": {"finesse": 1}, "effect": "Passive: Unarmed Melee attacks have an extended reach of 10ft."},
        "legs_slot": {"name": "Root Network", "stats": {"endurance": 1}, "effect": "Action: Once per encounter, root into the ground to heal 1d8 HP. Speed becomes 0."},
        "skin_slot": {"name": "Barkskin", "stats": {"vitality": 1}, "effect": "Passive: +2 Natural Defense. Cannot be inflicted with Poison status."},
        "special_slot": {"name": "Spore Burst", "stats": {"intuition": 1}, "effect": "Action: Once per encounter, release spores. Enemies within 10ft gain Disadvantage on next check."}
    },
    "REPTILE": {
        "head_slot": {"name": "Pit Organs", "stats": {"intuition": 1}, "effect": "Passive: Detect the exact location of warm-blooded creatures within 30ft."},
        "body_slot": {"name": "Cold-Blooded", "stats": {"logic": 1}, "effect": "Passive: Undetectable by thermal vision. Advantage on stealth in warm environments."},
        "arms_slot": {"name": "Toxic Claws", "stats": {"might": 1}, "effect": "Passive: Dealing melee damage applies 1 stack of Poison to the target."},
        "legs_slot": {"name": "Serpentine Slither", "stats": {"reflexes": 1}, "effect": "Passive: Ignore difficult terrain completely. Cannot be knocked prone."},
        "skin_slot": {"name": "Shed Skin", "stats": {"finesse": 1}, "effect": "Action: Once per cycle, instantly shed skin to remove all negative physical status effects."},
        "special_slot": {"name": "Regenerative Tissue", "stats": {"vitality": 1}, "effect": "Passive: During a rest cycle, automatically regenerate one severed limb and fully restore HP."}
    }
}

size_frames = [
    {"name": "Standard", "stats": {}, "effect": "Passive: Standard physical footprint. No penalties."},
    {"name": "Small Frame", "stats": {"reflexes": 1, "finesse": 1}, "effect": "Passive: Squeeze through tiny gaps. Advantage on Stealth."},
    {"name": "Light Frame", "stats": {"reflexes": 1}, "effect": "Passive: Trigger no pressure plates. Fall damage halved."},
    {"name": "Heavy Frame", "stats": {"might": 1}, "effect": "Passive: Provide Full Cover to allies. Cannot be shoved by medium creatures."},
    {"name": "Siege Frame", "stats": {"might": 1, "vitality": 1}, "effect": "Passive: Deal double damage to structures. Occupy a 10ft x 10ft space."}
]

ancestries = {
    "AQUATIC": ["Standard", "Selachimorpha Anatomy", "Crustacean Anatomy", "Cephalopod Anatomy", "Cetacean Anatomy", "Batoidea Anatomy", "Anguilliform Anatomy", "Cnidarian Anatomy", "Abyssal Anatomy"],
    "AVIAN": ["Standard", "Accipiter Anatomy", "Corvus Anatomy", "Strigiform Anatomy", "Psittacine Anatomy", "Waterfowl Anatomy", "Ratite Anatomy", "Spheniscid Anatomy", "Wading Anatomy"],
    "INSECT": ["Standard", "Coleoptera Anatomy", "Mantodea Anatomy", "Arachnid Anatomy", "Formicidae Anatomy", "Odonata Anatomy", "Scorpiones Anatomy", "Lepidoptera Anatomy", "Myriapod Anatomy"],
    "MAMMAL": ["Standard", "Bovine Anatomy", "Cervid Anatomy", "Primate Anatomy", "Ursine Anatomy", "Rodent Anatomy", "Bandit Anatomy", "Canine Anatomy", "Feline Anatomy"],
    "PLANT": ["Standard", "Arboreal Anatomy", "Floral Anatomy", "Creeper Anatomy", "Bush Anatomy", "Succulent Anatomy", "Fungal Anatomy", "Bryophyte Anatomy", "Pteridophyte Anatomy"],
    "REPTILE": ["Standard", "Crocodilian Anatomy", "Serpentine Anatomy", "Testudine Anatomy", "Climbing Anatomy", "Varanid Anatomy", "Chameleon Anatomy", "Theropod Anatomy", "Display Anatomy"]
}

slots_dict = {}
matrix_list = []

for species in species_list:
    slots_dict[species] = {}
    
    # 1. Sizes
    slots_dict[species]["size_slot"] = [s["name"] for s in size_frames]
    for sf in size_frames:
        if not any(entry["name"] == sf["name"] for entry in matrix_list):
            matrix_list.append({
                "name": sf["name"],
                "stats": sf["stats"],
                "passives": [{"name": f"{sf['name']} Trait", "effect": sf["effect"]}]
            })
            
    # 2. Ancestries (No stats, pure flavor)
    slots_dict[species]["ancestry_slot"] = ancestries[species]
    for anc in ancestries[species]:
        if not any(entry["name"] == anc for entry in matrix_list):
            matrix_list.append({
                "name": anc,
                "stats": {},
                "passives": [{"name": f"{anc} Trait", "effect": f"Flavor: Your species takes on the silhouette and minor cosmetic traits of {anc}."}]
            })

    # 3. Standard Slots (Head, Body, Arms, Legs, Skin, Special)
    for slot_name in ["head_slot", "body_slot", "arms_slot", "legs_slot", "skin_slot", "special_slot"]:
        # "Standard" as null choice, + Shared Traits + Unique Species Trait
        slot_choices = ["Standard"] + [t["name"] for t in shared_traits[slot_name]] + [unique_traits[species][slot_name]["name"]]
        slots_dict[species][slot_name] = slot_choices
        
        # Add Standard base placeholder if not already there
        if not any(entry["name"] == "Standard" for entry in matrix_list):
            matrix_list.append({
                "name": "Standard",
                "stats": {},
                "passives": [{"name": "Standard Trait", "effect": "No mutation selected."}]
            })

        # Add shared traits to matrix if not exists
        for t in shared_traits[slot_name]:
            if not any(entry["name"] == t["name"] for entry in matrix_list):
                matrix_list.append({
                    "name": t["name"],
                    "stats": t["stats"],
                    "passives": [{"name": f"{t['name']} Trait", "effect": t["effect"]}]
                })
        
        # Add unique trait to matrix
        ut = unique_traits[species][slot_name]
        matrix_list.append({
            "name": ut["name"],
            "stats": ut["stats"],
            "passives": [{"name": f"{ut['name']} Trait", "effect": ut["effect"]}]
        })

# Write to disk
os.makedirs("data", exist_ok=True)
os.makedirs("saga_vtt_client/src/data", exist_ok=True)

with open("data/Species_Slots.json", "w") as f1, open("saga_vtt_client/src/data/Species_Slots.json", "w") as f1_client:
    json.dump(slots_dict, f1, indent=2)
    json.dump(slots_dict, f1_client, indent=2)

with open("data/Evolution_Matrix.json", "w") as f2, open("saga_vtt_client/src/data/Evolution_Matrix.json", "w") as f2_client:
    json.dump(matrix_list, f2, indent=2)
    json.dump(matrix_list, f2_client, indent=2)

print("Evolutions generated successfully.")
