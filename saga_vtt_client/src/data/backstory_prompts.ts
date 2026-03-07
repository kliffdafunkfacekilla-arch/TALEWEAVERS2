export const HERITAGE_TERMINOLOGY: Record<string, string[]> = {
    MAMMAL: ["Cranial", "Brachial", "Femoral", "Axial", "Dermal", "Caudal"],
    REPTILE: ["Cranial", "Brachial", "Femoral", "Axial", "Dermal", "Caudal"],
    AQUATIC: ["Cranial", "Brachial", "Femoral", "Axial", "Dermal", "Caudal"],
    AVIAN: ["Cranial", "Brachial", "Femoral", "Axial", "Dermal", "Caudal"],
    INSECT: ["Cephalic", "Appendicular", "Anterior", "Thoraxial", "Cuticular", "Posterior"],
    PLANT: ["Apical", "Branching", "Rootborne", "Vascular", "Dermal", "Reproductive"]
};

// Internal slot mapping for heritages
export const HERITAGE_SLOTS = [
    "head_slot",    // 0: Cranial / Cephalic / Apical
    "arms_slot",    // 1: Brachial / Appendicular / Branching
    "legs_slot",    // 2: Femoral / Anterior / Rootborne
    "body_slot",    // 3: Axial / Thoraxial / Vascular
    "skin_slot",    // 4: Dermal / Cuticular / Dermal
    "special_slot"  // 5: Caudal / Posterior / Reproductive
];

export const BackstoryPrompts = {
    species: {
        question: "Into what biological family did your soul coalesce during the Great Weaving?",
        options: [
            { id: "MAMMAL", label: "Mammal", description: "Blood, fur, and the warmth of the hearth." },
            { id: "AVIAN", label: "Avian", description: "Feathers, hollow bone, and the reach of the wind." },
            { id: "REPTILE", label: "Reptile", description: "Scale, cold logic, and the patience of stone." },
            { id: "INSECT", label: "Insect", description: "Chitin, hive-memory, and the drive of the swarm." },
            { id: "PLANT", label: "Plant", description: "Root, photosynthesis, and the slow deep-thought." },
            { id: "AQUATIC", label: "Aquatic", description: "Gills, pressure-bound, and the secrets of the deep." }
        ]
    },
    size: {
        question: "What physical scale does your vessel present to the world?",
        slot: "size_slot"
    },
    ancestry: {
        question: "Which ancestral echoes define your lineage's specific form?",
        slot: "ancestry_slot"
    },
    heritages: {
        MAMMAL: {
            questions: [
                "How does your Cranial heritage perceive the world's anomalies?",
                "What strength lies within your Brachial heritage?",
                "How does your Femoral heritage traverse the rugged dustlands?",
                "In what way does your Axial heritage endure the aetheric pressure?",
                "What boundary does your Dermal heritage present to the elements?",
                "What unique trait manifests in your Caudal heritage?"
            ]
        },
        INSECT: {
            questions: [
                "How does your Cephalic heritage process the hive-pulse?",
                "What utility is found in your Appendicular heritge?",
                "How does your Anterior heretege steady your momentum?",
                "What resilience is found in your Thoraxial heretege?",
                "What protection is offered by your Cuticular heretege?",
                "What secret function is hidden in your Posterior heretege?"
            ]
        },
        PLANT: {
            questions: [
                "How does your Apical heritege reach toward the distant suns?",
                "What reach is found in your Branching heritege?",
                "How deep do the roots of your Rootborne heritege descend?",
                "What life-fluid flows through your Vascular heritege?",
                "What texture defines your Dermal heritege?",
                "How does your Reproductive heritege ensure the next bloom?"
            ]
        },
        // Fallback or Shared
        DEFAULT: {
            questions: [
                "How does your Cranial heritage perceive the world's anomalies?",
                "What strength lies within your Brachial heritage?",
                "How does your Femoral heritage traverse the rugged dustlands?",
                "In what way does your Axial heritage endure the aetheric pressure?",
                "What boundary does your Dermal heritage present to the elements?",
                "What unique trait manifests in your Caudal heritage?"
            ]
        }
    },
    triads: {
        Assault: {
            question: "When a predator cornered you in the dustlands, how did you respond?",
            options: [
                { skill: "Aggressive", label: "I struck first and hardest, leaving no room for a counter." },
                { skill: "Calculated", label: "I waited for the perfect opening, observing their flaw." },
                { skill: "Patient", label: "I out-endured them, yielding until they exhausted their fire." }
            ]
        },
        Coercion: {
            question: "How did you convince the stubborn gatekeepers to let you pass the aether-wall?",
            options: [
                { skill: "Intimidating", label: "I looked them in the eye until they flinched from my gaze." },
                { skill: "Deception", label: "I wove a web of lies so intricate they could not escape." },
                { skill: "Relentless", label: "I did not stop asking until their resolve finally crumbled." }
            ]
        },
        Ballistics: {
            question: "When you held your first range-tool, what instinct guided your hand?",
            options: [
                { skill: "Skirmish", label: "I stayed mobile, firing while closing the distance." },
                { skill: "Precise", label: "I held my breath, waiting for the perfect lethal point." },
                { skill: "Thrown/Tossed", label: "I used raw strength to hurl the projectile with force." }
            ]
        },
        Suppression: {
            question: "How do you handle a crowd of desperate scavengers blocking your path?",
            options: [
                { skill: "Predict", label: "I foresaw their movements and cut off their momentum." },
                { skill: "Impose", label: "I projected a presence so heavy they yielded without a word." },
                { skill: "Imply", label: "I made the consequence of blocking me painfully clear." }
            ]
        },
        Fortify: {
            question: "What was your stance during the Great Siege of the Silent Spire?",
            options: [
                { skill: "Rooted", label: "I stood like a mountain, unmoving against the tide." },
                { skill: "Fluid", label: "I moved with the blows, redirecting their force away." },
                { skill: "Dueling", label: "I met their steel with my own, winning every clash." }
            ]
        },
        Resolve: {
            question: "How did you maintain your mind during the nights of the Umbral Eclipse?",
            options: [
                { skill: "Confidence", label: "I held fast to my inner worth, refusing to let shadows in." },
                { skill: "Reasoning", label: "I analyzed the fear away with cold, hard logic." },
                { skill: "Cavalier", label: "I mocked the darkness, daring it to try and break me." }
            ]
        },
        Operations: {
            question: "What was your contribution to the reconstruction of the Vessels?",
            options: [
                { skill: "Alter", label: "I reshaped the very environment to suit our needs." },
                { skill: "Utilize", label: "I found use for every scrap and tool available." },
                { skill: "Introduce", label: "I reinforced our structures, making them unbreakable." }
            ]
        },
        Tactics: {
            question: "When your band was surrounded by the Hive-Swarm, how did you lead?",
            options: [
                { skill: "Command", label: "I gave the orders that kept our lines from breaking." },
                { skill: "Exploit", label: "I identified the swarm-lead and struck the opening." },
                { skill: "Tactics", label: "I optimized our formation for maximum speed and reach." }
            ]
        },
        Stabilize: {
            question: "What did you do when the Soulweave first began to unravel in your kin?",
            options: [
                { skill: "First Aid", label: "I acted quickly, stitching the spirit back together." },
                { skill: "Medicine", label: "I used the deep-lore of herbs to purge the decay." },
                { skill: "Surgery", label: "I cut away the corruption with a steady, surgical hand." }
            ]
        },
        Rally: {
            question: "How did you hearten your allies after the failure at the Void-Gate?",
            options: [
                { skill: "Self-Awareness", label: "I helped them face their own shadows to find strength." },
                { skill: "Detached", label: "I focused them on the data, removing the sting of loss." },
                { skill: "Mindfulness", label: "I shared the burden, linking our spirits in meditation." }
            ]
        },
        Mobility: {
            question: "When the Toxic Fog rolled in, how did you survive the escape?",
            options: [
                { skill: "Charge", label: "I burst through the thickest part with raw momentum." },
                { skill: "Flanking", label: "I found the side-paths that the fog had not yet claimed." },
                { skill: "Speed", label: "I was simply faster than the encroaching gloom." }
            ]
        },
        Bravery: {
            question: "What drove you to step into the unstable Aether-Cloud?",
            options: [
                { skill: "Commitment", label: "I gave my word to see it through, regardless of cost." },
                { skill: "Determined", label: "I would not be the one to turn back while others walked." },
                { skill: "Outsmart", label: "I knew exactly when the cloud would pulse and acted." }
            ]
        }
    },
    schools: {
        prime: {
            question: "Which aspect of the Soulweave did you first learn to command as your Prime discipline?",
            options: [
                { id: "MIGHT", label: "The Nexus (Might)", description: "Commanding gravity, tension, and raw physical force." },
                { id: "KNOWLEDGE", label: "The Ratio (Knowledge)", description: "Calculated analysis and pure telekinetic will." },
                { id: "AWARENESS", label: "The Echo (Awareness)", description: "Sensing the unseen threads of the manifest world." },
                { id: "VITALITY", label: "The Vita (Vitality)", description: "Governing the growth and repair of biological form." },
                { id: "LOGIC", label: "The Ordo (Logic)", description: "Geometric precision and elemental alchemy." },
                { id: "FORTITUDE", label: "The Lex (Fortitude)", description: "Unbending rules and immunity to the chaotic aether." }
            ]
        },
        aux: {
            question: "What secondary echo resonates within your spirit as an Auxiliary school?",
            options: [
                { id: "MIGHT", label: "The Nexus (Might)", description: "Commanding gravity, tension, and raw physical force." },
                { id: "KNOWLEDGE", label: "The Ratio (Knowledge)", description: "Calculated analysis and pure telekinetic will." },
                { id: "AWARENESS", label: "The Echo (Awareness)", description: "Sensing the unseen threads of the manifest world." },
                { id: "VITALITY", label: "The Vita (Vitality)", description: "Governing the growth and repair of biological form." },
                { id: "LOGIC", label: "The Ordo (Logic)", description: "Geometric precision and elemental alchemy." },
                { id: "FORTITUDE", label: "The Lex (Fortitude)", description: "Unbending rules and immunity to the chaotic aether." }
            ]
        }
    },
    catalyst: {
        question: "What was the defining tragedy or triumph—the Catalyst—that forced you onto your current journey?",
        options: [
            {
                id: "ORPHAN",
                label: "The Dustland Orphan",
                description: "You scavenged to survive in the abrasive wastes.",
                gear: { "main_hand": "wpn_rusted_cleaver", "consumable_1": "csm_travelers_bread" },
                backstory: "Raised in the shifting dust, you learned that nothing is permanent except your will."
            },
            {
                id: "NOBLE",
                label: "The Discarded Noble",
                description: "You were cast out from the Spire, stripped of your rank.",
                gear: { "main_hand": "wpn_steel_rapier", "consumable_1": "csm_stamina_tea" },
                backstory: "High-born and low-driven, you seek to reclaim what the aether took from you."
            },
            {
                id: "SCAVENGER",
                label: "The Aether-Struck Scavenger",
                description: "A pulse of raw magic changed your perspective—literally.",
                gear: { "main_hand": "wpn_hunting_bow", "consumable_1": "csm_ddust" },
                backstory: "You saw the code behind the veil, and now you can never unsee it."
            }
        ]
    }
};
