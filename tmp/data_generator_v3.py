import json
import os

species_list = ["AQUATIC", "AVIAN", "INSECT", "MAMMAL", "PLANT", "REPTILE"]

size_frames = [
    {"name": "Standard", "stats": {}, "effect": "Passive: Standard physical footprint. No penalties."},
    {"name": "Small Frame", "stats": {"reflexes": 1, "finesse": 1, "might": -1, "vitality": -1}, "effect": "Passive: Squeeze through tiny gaps. Advantage on Stealth."},
    {"name": "Light Frame", "stats": {"reflexes": 1, "might": -1}, "effect": "Passive: Trigger no pressure plates. Fall damage halved."},
    {"name": "Heavy Frame", "stats": {"might": 1, "reflexes": -1}, "effect": "Passive: Provide Full Cover to allies. Cannot be shoved by medium creatures."},
    {"name": "Siege Frame", "stats": {"might": 2, "vitality": 1, "reflexes": -2, "finesse": -1}, "effect": "Passive: Deal double damage to structures. Occupy a 10ft x 10ft space."}
]

# Ancestries with +1/-1 and passives
ancestries = {
    "AQUATIC": [
        {"name": "Standard", "stats": {}, "effect": "No mutation selected."},
        {"name": "Selachimorpha Anatomy", "stats": {"might": 1, "charm": -1}, "effect": "Passive: Blood Scent (Advantage tracking wounded enemies)."},
        {"name": "Crustacean Anatomy", "stats": {"fortitude": 1, "reflexes": -1}, "effect": "Passive: Hard Shell (Resist slashing from small weapons)."},
        {"name": "Cephalopod Anatomy", "stats": {"intuition": 1, "endurance": -1}, "effect": "Passive: Boneless (Escape all non-magical restraints)."},
        {"name": "Cetacean Anatomy", "stats": {"endurance": 1, "finesse": -1}, "effect": "Passive: Deep Diver (Hold breath for 2 hours)."},
        {"name": "Batoidea Anatomy", "stats": {"finesse": 1, "might": -1}, "effect": "Passive: Flat Profile (Advantage hiding in sand/mud)."},
        {"name": "Cnidarian Anatomy", "stats": {"vitality": 1, "logic": -1}, "effect": "Passive: Numbing Touch (Unarmed strikes slow targets)."}
    ],
    "AVIAN": [
        {"name": "Standard", "stats": {}, "effect": "No mutation selected."},
        {"name": "Accipiter Anatomy", "stats": {"reflexes": 1, "endurance": -1}, "effect": "Passive: Raptor Dive (Advantage on attacks made while falling)."},
        {"name": "Corvus Anatomy", "stats": {"logic": 1, "might": -1}, "effect": "Passive: Tool User (Can craft basic items without kits)."},
        {"name": "Strigiform Anatomy", "stats": {"awareness": 1, "vitality": -1}, "effect": "Passive: Silent Flight (No noise while hovering)."},
        {"name": "Psittacine Anatomy", "stats": {"charm": 1, "fortitude": -1}, "effect": "Passive: Mimicry (Perfectly copy voices)."},
        {"name": "Waterfowl Anatomy", "stats": {"endurance": 1, "reflexes": -1}, "effect": "Passive: Waterproof (Immune to cold water penalties)."},
        {"name": "Ratite Anatomy", "stats": {"might": 1, "intuition": -1}, "effect": "Passive: Thunder Kicks (Unarmed attacks push targets 5ft)."}
    ],
    "INSECT": [
        {"name": "Standard", "stats": {}, "effect": "No mutation selected."},
        {"name": "Coleoptera Anatomy", "stats": {"fortitude": 1, "finesse": -1}, "effect": "Passive: Iron Shell (Can use body to block small openings)."},
        {"name": "Mantodea Anatomy", "stats": {"finesse": 1, "endurance": -1}, "effect": "Passive: Ambush Predator (Advantage on first strike from stealth)."},
        {"name": "Arachnid Anatomy", "stats": {"knowledge": 1, "charm": -1}, "effect": "Passive: Web Weaver (Create traps over short cycles)."},
        {"name": "Formicidae Anatomy", "stats": {"might": 1, "intuition": -1}, "effect": "Passive: Ant Strength (Carry 5x normal weight)."},
        {"name": "Odonata Anatomy", "stats": {"reflexes": 1, "vitality": -1}, "effect": "Passive: Hover Flight (Can stop mid-air without falling)."},
        {"name": "Lepidoptera Anatomy", "stats": {"charm": 1, "might": -1}, "effect": "Passive: Hypnotic Patterns (Advantage to charm beasts)."}
    ],
    "MAMMAL": [
        {"name": "Standard", "stats": {}, "effect": "No mutation selected."},
        {"name": "Bovine Anatomy", "stats": {"endurance": 1, "finesse": -1}, "effect": "Passive: Iron Stomach (Immune to ingested poisons)."},
        {"name": "Primate Anatomy", "stats": {"finesse": 1, "fortitude": -1}, "effect": "Passive: Ape Grip (Climb without tools)."},
        {"name": "Ursine Anatomy", "stats": {"might": 1, "reflexes": -1}, "effect": "Passive: Bear Hug (Advantage to maintain grapples)."},
        {"name": "Rodent Anatomy", "stats": {"reflexes": 1, "might": -1}, "effect": "Passive: Nibble (Can chew through ropes or wood easily)."},
        {"name": "Canine Anatomy", "stats": {"awareness": 1, "logic": -1}, "effect": "Passive: Pack Tactics (Advantage when allied to target)."},
        {"name": "Feline Anatomy", "stats": {"intuition": 1, "endurance": -1}, "effect": "Passive: Nine Lives (Take minimum fall damage always)."}
    ],
    "PLANT": [
        {"name": "Standard", "stats": {}, "effect": "No mutation selected."},
        {"name": "Arboreal Anatomy", "stats": {"fortitude": 1, "reflexes": -1}, "effect": "Passive: Deep Roots (Resist forced movement)."},
        {"name": "Floral Anatomy", "stats": {"charm": 1, "might": -1}, "effect": "Passive: Alluring Scent (Advantage on persuasion checks)."},
        {"name": "Creeper Anatomy", "stats": {"finesse": 1, "logic": -1}, "effect": "Passive: Vine Reach (Can grasp items from 10ft)."},
        {"name": "Succulent Anatomy", "stats": {"endurance": 1, "intuition": -1}, "effect": "Passive: Water Hoard (Go months without drinking)."},
        {"name": "Fungal Anatomy", "stats": {"intuition": 1, "charm": -1}, "effect": "Passive: Spore Network (Feel vibrations through soil)."},
        {"name": "Bryophyte Anatomy", "stats": {"vitality": 1, "might": -1}, "effect": "Passive: Moss Bed (Rest in any environment safely)."}
    ],
    "REPTILE": [
        {"name": "Standard", "stats": {}, "effect": "No mutation selected."},
        {"name": "Crocodilian Anatomy", "stats": {"might": 1, "finesse": -1}, "effect": "Passive: Vice Jaws (Lock onto targets dealing DOT)."},
        {"name": "Serpentine Anatomy", "stats": {"finesse": 1, "fortitude": -1}, "effect": "Passive: Coil (Can fit into spaces 1/3 your size)."},
        {"name": "Testudine Anatomy", "stats": {"endurance": 1, "reflexes": -1}, "effect": "Passive: Shell Retreat (Action to gain +5 Natural Defense, lose movement)."},
        {"name": "Varanid Anatomy", "stats": {"intuition": 1, "charm": -1}, "effect": "Passive: Forked Tongue (Advantage on insight checks)."},
        {"name": "Chameleon Anatomy", "stats": {"awareness": 1, "might": -1}, "effect": "Passive: Active Camo (Advantage on stealth)."},
        {"name": "Theropod Anatomy", "stats": {"reflexes": 1, "logic": -1}, "effect": "Passive: Raptor Sprint (Move speed increases every turn moving straight)."}
    ]
}

# The 4 archetypes (Tank, Scout, Mage, Support) map to specific stats
# Tank: Fortitude, Endurance, Might
# Scout: Awareness, Reflexes, Finesse
# Mage: Logic, Willpower, Knowledge
# Support: Charm, Intuition, Vitality

head_archetypes = {
    "AQUATIC": [
        {"name": "Armored Melon", "stats": {"fortitude": 1}, "effect": "Passive: Advantage vs Stun. Can ram objects safely."},
        {"name": "Lateral Line", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Perception. Detect currents and pressure changes."},
        {"name": "Electrosensory Organ", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack by overriding enemy nervous system."},
        {"name": "Whale Song Chamber", "stats": {"charm": 1}, "effect": "Passive: Allies within 30ft hear you perfectly even underwater. Advantage on Social Intimidation/Persuasion."}
    ],
    "AVIAN": [
        {"name": "Reinforced Beak Base", "stats": {"fortitude": 1}, "effect": "Passive: Advantage vs Stun. Unarmed headbutts deal piercing damage."},
        {"name": "Tubular Eyes", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Perception. Perfect telescopic vision."},
        {"name": "Magnetic Compass", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack by aligning with leylines."},
        {"name": "Vocal Crest", "stats": {"charm": 1}, "effect": "Passive: Allies within 30ft hear you perfectly. Advantage on Social Performance."}
    ],
    "INSECT": [
        {"name": "Chitinous Mandibles", "stats": {"fortitude": 1}, "effect": "Passive: Advantage vs Stun. Bites can sever thin ropes."},
        {"name": "Antennae Array", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Perception. Detect changes in air pressure."},
        {"name": "Neural Ganglia", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack through accelerated processing."},
        {"name": "Stridulation Organs", "stats": {"charm": 1}, "effect": "Passive: Allies within 30ft hear you perfectly. Advantage on Social Intimidation."}
    ],
    "MAMMAL": [
        {"name": "Thick Skull", "stats": {"fortitude": 1}, "effect": "Passive: Advantage vs Stun. Headbutts deal bludgeoning damage."},
        {"name": "Swivel Ears", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Perception. Detect whispers through walls."},
        {"name": "Expanded Cranium", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack."},
        {"name": "Roar Box", "stats": {"charm": 1}, "effect": "Passive: Allies within 30ft hear you perfectly. Advantage on Social Intimidation."}
    ],
    "PLANT": [
        {"name": "Iron-Bark Crown", "stats": {"fortitude": 1}, "effect": "Passive: Advantage vs Stun. Immune to head-trauma."},
        {"name": "Chemoreceptor Petals", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Perception. Detect airborne toxins instantly."},
        {"name": "Mycelial Node", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack through network computing."},
        {"name": "Spore Emitter", "stats": {"charm": 1}, "effect": "Passive: Pheromones make allies hear you instinctively. Advantage on Social Persuasion."}
    ],
    "REPTILE": [
        {"name": "Bony Crest", "stats": {"fortitude": 1}, "effect": "Passive: Advantage vs Stun. Deflects overhead strikes."},
        {"name": "Heat-Sensing Pits", "stats": {"awareness": 1}, "effect": "Passive: Advantage on Perception. See thermal signatures."},
        {"name": "Parietal Eye", "stats": {"logic": 1}, "effect": "Action: Once per encounter, gain Advantage on a Mental attack with a focused stare."},
        {"name": "Throat Pouch", "stats": {"charm": 1}, "effect": "Passive: Resonant croaks aid allies within 30ft. Advantage on Social Intimidation."}
    ]
}

body_archetypes = {
    "AQUATIC": [
        {"name": "Dermal Denticles", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense. Damage to unarmed attackers."},
        {"name": "Cartilaginous Spine", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks."},
        {"name": "Osmotic Gland", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus by filtering ambient magic."},
        {"name": "Bioluminescent Lure", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ],
    "AVIAN": [
        {"name": "Keel Bone", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense. Protects vitals."},
        {"name": "Articulated Vertebrae", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks. 180-degree neck turn."},
        {"name": "Hollow Conduit", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus via resonant breathing."},
        {"name": "Iridescent Plumage", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ],
    "INSECT": [
        {"name": "Thoracic Plates", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense."},
        {"name": "Segmented Abdomen", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks."},
        {"name": "Aetheric Spinneret", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus by weaving raw magic."},
        {"name": "Calming Pheromones", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ],
    "MAMMAL": [
        {"name": "Density Plating", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense."},
        {"name": "Feline Agility", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks."},
        {"name": "Aura Battery", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus."},
        {"name": "Musk Emitter", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ],
    "PLANT": [
        {"name": "Heartwood Core", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense."},
        {"name": "Vine-Laced Torso", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks."},
        {"name": "Sap Channel", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus from the earth."},
        {"name": "Sweet Nectar", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ],
    "REPTILE": [
        {"name": "Osteoderms", "stats": {"endurance": 1}, "effect": "Passive: +2 Natural Defense."},
        {"name": "Serpentine Coils", "stats": {"reflexes": 1}, "effect": "Passive: Advantage on Acrobatics and Squeezing checks."},
        {"name": "Solar Node", "stats": {"willpower": 1}, "effect": "Action: Once per cycle, regain 1d4 Focus while in sunlight/heat."},
        {"name": "Mesmerizing Scales", "stats": {"intuition": 1}, "effect": "Passive: Advantage on Social checks to calm or subtly influence others."}
    ]
}

arms_archetypes = {
    "AQUATIC": [
        {"name": "Crustacean Pincers", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Fin Blades", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Water-Weaver Hands", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away through water manipulation."},
        {"name": "Urchin Bracers", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ],
    "AVIAN": [
        {"name": "Bone-Club Wings", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Razor Feathers", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Aero-Channeled Palms", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away."},
        {"name": "Protective Wingspan", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ],
    "INSECT": [
        {"name": "Crushing Claws", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Serrated Forelegs", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Silk-Spun Conduits", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away via silk threads."},
        {"name": "Carapace Gauntlets", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ],
    "MAMMAL": [
        {"name": "Heavy Paws", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Retractable Claws", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Runic Palms", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away."},
        {"name": "Guardian Forearms", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ],
    "PLANT": [
        {"name": "Burl Fists", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Thorned Appendages", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Vine Extension", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away."},
        {"name": "Branch Buckler", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ],
    "REPTILE": [
        {"name": "Clubbed Wrists", "stats": {"might": 1}, "effect": "Passive: Unarmed strikes do 1d6 Bludgeoning. Advantage on lifting heavy limits."},
        {"name": "Sickle Claws", "stats": {"finesse": 1}, "effect": "Passive: Unarmed strikes do 1d4 Slashing. Advantage on Sleight of Hand."},
        {"name": "Astral Scales", "stats": {"knowledge": 1}, "effect": "Passive: Touch-based spells or skills can be executed up to 10ft away."},
        {"name": "Scute Gauntlets", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, grant an adjacent ally Advantage on their next Defense check."}
    ]
}

legs_archetypes = {
    "AQUATIC": [
        {"name": "Anchor Tail", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Hydro-Propulsion", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Buoyancy Bladders", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Dorsal Sprint", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ],
    "AVIAN": [
        {"name": "Locking Talons", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Launch Pads", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Minor Levitation", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Flock Leader Stride", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ],
    "INSECT": [
        {"name": "Six-Legged Stance", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Grasshopper Joints", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Gossamer Wings", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Swarm-Rush", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ],
    "MAMMAL": [
        {"name": "Stout Legs", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Spring Tendons", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Aether Paws", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Rescue Dash", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ],
    "PLANT": [
        {"name": "Deep Roots", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Tumbleweed Bound", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Spore Cloud Cushion", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Branching Stride", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ],
    "REPTILE": [
        {"name": "Heavy Tail Counterbalance", "stats": {"fortitude": 1}, "effect": "Passive: Cannot be knocked Prone while conscious."},
        {"name": "Coiled Muscles", "stats": {"reflexes": 1}, "effect": "Passive: +10ft Movement Speed. Advantage on Jump checks."},
        {"name": "Thermal Draft Lift", "stats": {"logic": 1}, "effect": "Passive: Hover 1ft off the ground, ignoring floor-based hazards and difficult terrain."},
        {"name": "Cold-Blooded Dash", "stats": {"charm": 1}, "effect": "Passive: When you move towards an ally in danger, gain +5ft bonus movement speed."}
    ]
}

skin_archetypes = {
    "AQUATIC": [
        {"name": "Placoid Scales", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Cuttlefish Camouflage", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Abyssal Pressure Skin", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Soothing Mist", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ],
    "AVIAN": [
        {"name": "Thick Leather", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Plumage Blending", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Song-Woven Feathers", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Calming Down", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ],
    "INSECT": [
        {"name": "Iron Carapace", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Stick-Bug Disguise", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Hive-Mind Coating", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Pheromone Solace", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ],
    "MAMMAL": [
        {"name": "Calloused Hide", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Chroma-Fur", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Runic Scarring", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Comforting Presence", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ],
    "PLANT": [
        {"name": "Cork Bark", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Leafy Concealment", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Spirit-Wood", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Aromatherapy Blooms", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ],
    "REPTILE": [
        {"name": "Hardened Scutes", "stats": {"endurance": 1}, "effect": "Passive: Resistance to Slashing damage."},
        {"name": "Chameleon Scales", "stats": {"finesse": 1}, "effect": "Passive: Advantage on Stealth checks when remaining stationary."},
        {"name": "Dragon-Mind Runes", "stats": {"willpower": 1}, "effect": "Passive: Resistance to Mental and Psychic damage."},
        {"name": "Basking Warmth", "stats": {"intuition": 1}, "effect": "Passive: Adjacent allies dynamically regain 1 Composure at the start of their turn."}
    ]
}

special_archetypes = {
    "AQUATIC": [
        {"name": "Current Surge", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Abyssal Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Oceanic Calm", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower/Fortitude Check."},
        {"name": "Leviathan's Bellow", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ],
    "AVIAN": [
        {"name": "Dive-Bomb Surge", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Feather Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Sky-Mind", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower/Fortitude Check."},
        {"name": "Eagle Cry", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ],
    "INSECT": [
        {"name": "Swarm Frenzy", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Burrow Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Hive Logic", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower/Fortitude Check."},
        {"name": "Queen's Command", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ],
    "MAMMAL": [
        {"name": "Adrenaline Surge", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Shadow Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Mind Blank", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower/Fortitude Check."},
        {"name": "Rallying Cry", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ],
    "PLANT": [
        {"name": "Overgrowth Surge", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Root Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Forest Wisdom", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower/Fortitude Check."},
        {"name": "Blossoming Aura", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ],
    "REPTILE": [
        {"name": "Cold-Blooded Fury", "stats": {"might": 1}, "effect": "Action: Once per cycle, instantly gain an additional Action on your turn."},
        {"name": "Slither Step", "stats": {"awareness": 1}, "effect": "Action: Once per encounter, teleport 15ft to an unoccupied space you can see."},
        {"name": "Ancient Serenity", "stats": {"knowledge": 1}, "effect": "Action: Once per cycle, instantly succeed on a Willpower/Fortitude Check."},
        {"name": "Dragon's Roar", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, all allies within 30ft gain Advantage on their next attack check."}
    ]
}


unique_traits = {
    "AQUATIC": {
        "head_slot": {"name": "Lateral Electrolocation", "stats": {"logic": 1}, "effect": "Passive: Detect invisible enemies within 15ft in water."},
        "body_slot": {"name": "Ink-Filled Bladder", "stats": {"finesse": 1}, "effect": "Action: Once per encounter, drop a cloud of ink that grants full concealment."},
        "arms_slot": {"name": "Nematocyst Stingers", "stats": {"vitality": 1}, "effect": "Action: Once per encounter, paralyze a grabbed opponent."},
        "legs_slot": {"name": "Reverse Webbing", "stats": {"endurance": 1}, "effect": "Passive: Advantage on checks to swim against strong currents."},
        "skin_slot": {"name": "Bioluminescent Patterns", "stats": {"charm": 1}, "effect": "Action: Flash a hypnotic pattern (Once per encounter, distract enemy)."},
        "special_slot": {"name": "Starfish Regeneration", "stats": {"fortitude": 1}, "effect": "Passive: Regrow lost limbs over a single cycle."}
    },
    "AVIAN": {
        "head_slot": {"name": "Gyro-Stabilized Head", "stats": {"reflexes": 1}, "effect": "Passive: Immune to vertigo and disorientation."},
        "body_slot": {"name": "Crop Pouch", "stats": {"endurance": 1}, "effect": "Passive: Can store tiny objects or food internally."},
        "arms_slot": {"name": "Swept-Back Pinions", "stats": {"finesse": 1}, "effect": "Passive: +5ft flying speed. Advantage on aerial dodges."},
        "legs_slot": {"name": "Zygodactyl Grip", "stats": {"might": 1}, "effect": "Passive: Cannot be disarmed of weapons held by feet. Can hang upside down indefinitely."},
        "skin_slot": {"name": "Preen Oil", "stats": {"vitality": 1}, "effect": "Passive: Immune to water-based debuffs."},
        "special_slot": {"name": "Boom-Sack", "stats": {"charm": 1}, "effect": "Action: Release a deafening call (Once per encounter, minor thunder damage in 10ft)."}
    },
    "INSECT": {
        "head_slot": {"name": "Pheromone Receptors", "stats": {"intuition": 1}, "effect": "Passive: Detect fear or aggression via scent."},
        "body_slot": {"name": "Elytra Shells", "stats": {"fortitude": 1}, "effect": "Passive: Wings act as a shield to your back (+1 Defense to back attacks)."},
        "arms_slot": {"name": "Spinneret Wrists", "stats": {"knowledge": 1}, "effect": "Action: Shoot 20ft of adhesive silk (Once per encounter, roots target)."},
        "legs_slot": {"name": "Hydraulic Knees", "stats": {"might": 1}, "effect": "Passive: Jump distance is tripled from a standing start."},
        "skin_slot": {"name": "Micro-Hairs", "stats": {"awareness": 1}, "effect": "Passive: Sense invisible or extremely quiet enemies standing near you."},
        "special_slot": {"name": "Molting Hormone", "stats": {"vitality": 1}, "effect": "Action: Escape any biological restraint or grapple automatically (Once per encounter)."}
    },
    "MAMMAL": {
        "head_slot": {"name": "Tapetum Lucidum", "stats": {"awareness": 1}, "effect": "Passive: Darkvision 60ft."},
        "body_slot": {"name": "Blubber/Fat Store", "stats": {"endurance": 1}, "effect": "Passive: Ignore starvation penalties for 1 week."},
        "arms_slot": {"name": "Dexterous Digits", "stats": {"logic": 1}, "effect": "Passive: Advantage on lockpicking or mechanism disable."},
        "legs_slot": {"name": "Padded Soles", "stats": {"finesse": 1}, "effect": "Passive: Silence movement perfectly. Footsteps leave no sound."},
        "skin_slot": {"name": "Oily Coat", "stats": {"vitality": 1}, "effect": "Passive: Advantage to slip through tight bindings."},
        "special_slot": {"name": "Prehensile Tail", "stats": {"reflexes": 1}, "effect": "Passive: Can hold items or weapons (but not attack with them)."}
    },
    "PLANT": {
        "head_slot": {"name": "Thermal Pits", "stats": {"awareness": 1}, "effect": "Passive: See heat effectively out to 30ft."},
        "body_slot": {"name": "Hydraulic Torso", "stats": {"might": 1}, "effect": "Passive: Add Fortitude bonus to lifting capacity."},
        "arms_slot": {"name": "Fly-Trap Jaws", "stats": {"fortitude": 1}, "effect": "Action: Melee attack that automatically grapples target (Once per encounter)."},
        "legs_slot": {"name": "Drill Roots", "stats": {"endurance": 1}, "effect": "Action: Burrow 10ft into soft earth."},
        "skin_slot": {"name": "Photosynthetic Membrane", "stats": {"knowledge": 1}, "effect": "Passive: Advantage on checks to survive outdoors."},
        "special_slot": {"name": "Pollen Cloud", "stats": {"charm": 1}, "effect": "Action: Hallucinogenic cloud (Once per cycle, confuse enemies in 15ft)."}
    },
    "REPTILE": {
        "head_slot": {"name": "Nictitating Membrane", "stats": {"endurance": 1}, "effect": "Passive: Immune to blinding dirt or dust."},
        "body_slot": {"name": "Stem-Cell Core", "stats": {"vitality": 1}, "effect": "Passive: Advantage on checks to heal critical injuries."},
        "arms_slot": {"name": "Van der Waals Pads", "stats": {"reflexes": 1}, "effect": "Passive: Climb glass and sheer surfaces effortlessly."},
        "legs_slot": {"name": "Paddle Tail", "stats": {"finesse": 1}, "effect": "Passive: Swim speed equals walk speed."},
        "skin_slot": {"name": "Solar Scales", "stats": {"willpower": 1}, "effect": "Passive: Convert extreme heat into temporary hit points (Once per cycle)."},
        "special_slot": {"name": "Autotomy Tail", "stats": {"logic": 1}, "effect": "Action: Drop tail to escape a grapple or fatal blow instantly (Regrows over 1 cycle)."}
    }
}

slots_dict = {}
matrix_list = []
seen_names = set()

def add_to_matrix(entry):
    if entry["name"] not in seen_names:
        matrix_list.append(entry)
        seen_names.add(entry["name"])

# 1. Size
for sf in size_frames:
    add_to_matrix({
        "name": sf["name"],
        "stats": sf["stats"],
        "passives": [{"name": f"{sf['name']} Trait", "effect": sf["effect"]}]
    })

# Add standard placeholder
add_to_matrix({
    "name": "Standard",
    "stats": {},
    "passives": [{"name": "Standard Trait", "effect": "No mutation selected."}]
})

for species in species_list:
    slots_dict[species] = {}
    
    # size slot
    slots_dict[species]["size_slot"] = [s["name"] for s in size_frames]
    
    # ancestry slot
    slots_dict[species]["ancestry_slot"] = [anc["name"] for anc in ancestries[species]]
    for anc in ancestries[species]:
        add_to_matrix({
            "name": anc["name"],
            "stats": anc["stats"],
            "passives": [{"name": f"{anc['name']} Ancestry", "effect": anc["effect"]}]
        })
        
    # loop over 6 body slots
    slots = ["head_slot", "body_slot", "arms_slot", "legs_slot", "skin_slot", "special_slot"]
    archetype_maps = [head_archetypes, body_archetypes, arms_archetypes, legs_archetypes, skin_archetypes, special_archetypes]
    
    for slot_name, arch_map in zip(slots, archetype_maps):
        slot_choices = ["Standard"]
        
        # archetypes
        for arch in arch_map[species]:
            slot_choices.append(arch["name"])
            add_to_matrix({
                "name": arch["name"],
                "stats": arch["stats"],
                "passives": [{"name": f"{arch['name']} Trait", "effect": arch["effect"]}]
            })
            
        # unique trait
        ut = unique_traits[species][slot_name]
        slot_choices.append(ut["name"])
        add_to_matrix({
            "name": ut["name"],
            "stats": ut["stats"],
            "passives": [{"name": f"{ut['name']} Trait", "effect": ut["effect"]}]
        })
        
        slots_dict[species][slot_name] = slot_choices

# Write to disk
os.makedirs("data", exist_ok=True)
os.makedirs("saga_vtt_client/src/data", exist_ok=True)

with open("data/Species_Slots.json", "w") as f1, open("saga_vtt_client/src/data/Species_Slots.json", "w") as f1_client:
    json.dump(slots_dict, f1, indent=2)
    json.dump(slots_dict, f1_client, indent=2)

with open("data/Evolution_Matrix.json", "w") as f2, open("saga_vtt_client/src/data/Evolution_Matrix.json", "w") as f2_client:
    json.dump(matrix_list, f2, indent=2)
    json.dump(matrix_list, f2_client, indent=2)

print("Evolutions generated successfully with flavor and ancestry adjustments.")
