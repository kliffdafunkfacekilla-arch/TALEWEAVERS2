import json
import os

tactical_triads = {
  "Assault": [
    {
      "skill": "Aggressive",
      "stat_pair": "Might + Knowledge",
      "effect": "Passive: Advantage on damage rolls against enemies with heavy Natural Defense or Shields."
    },
    {
      "skill": "Calculated",
      "stat_pair": "Reflexes + Logic",
      "effect": "Action: Once per encounter, declare a weak point. Gain Advantage on your next Attack check against that target."
    },
    {
      "skill": "Patient",
      "stat_pair": "Finesse + Intuition",
      "effect": "Passive: If you took no offensive actions on your last turn, gain Advantage on your first Attack check this turn."
    }
  ],
  "Coercion": [
    {
      "skill": "Intimidating",
      "stat_pair": "Vitality + Charm",
      "effect": "Action: Once per encounter, force a target to roll a Composure Check with Disadvantage or be Frightened for 1 turn."
    },
    {
      "skill": "Deception",
      "stat_pair": "Endurance + Willpower",
      "effect": "Passive: Advantage on Social checks when attempting to lie, bluff, or feint in combat."
    },
    {
      "skill": "Relentless",
      "stat_pair": "Fortitude + Awareness",
      "effect": "Passive: Deal 1d4 direct Composure damage to a target when you successfully strike them with a melee attack."
    }
  ],
  "Ballistics": [
    {
      "skill": "Skirmish",
      "stat_pair": "Reflexes + Knowledge",
      "effect": "Passive: You do not suffer Disadvantage when making ranged attacks in close-quarters (within 5ft)."
    },
    {
      "skill": "Precise",
      "stat_pair": "Finesse + Logic",
      "effect": "Action: Once per cycle, gain Advantage on a Critical Injury Check to cripple a target's limb."
    },
    {
      "skill": "Thrown/Tossed",
      "stat_pair": "Might + Awareness",
      "effect": "Action: Once per encounter, throw an object or weapon with such force the target must pass a Fortitude Check or be Staggered."
    }
  ],
  "Suppression": [
    {
      "skill": "Predict",
      "stat_pair": "Vitality + Intuition",
      "effect": "Action: Once per cycle, declare a hex. Any enemy entering it must pass a Willpower Check or their movement drops to 0."
    },
    {
      "skill": "Impose",
      "stat_pair": "Fortitude + Willpower",
      "effect": "Passive: Enemies within 10ft of you suffer Disadvantage on Initiative rolls."
    },
    {
      "skill": "Imply",
      "stat_pair": "Endurance + Charm",
      "effect": "Action: Once per encounter, subtly threaten a target. They suffer Disadvantage on their next offensive action unless they move out of Line of Sight."
    }
  ],
  "Fortify": [
    {
      "skill": "Rooted",
      "stat_pair": "Endurance + Logic",
      "effect": "Passive: Immune to Forced Movement. Advantage on checks to resist being Disarmed."
    },
    {
      "skill": "Fluid",
      "stat_pair": "Fortitude + Knowledge",
      "effect": "Action: Once per cycle, automatically convert a Solid Hit against you into a Graze (half damage)."
    },
    {
      "skill": "Dueling",
      "stat_pair": "Might + Intuition",
      "effect": "Passive: Winning an opposed Clash roll grants Advantage on your next Assault action against that opponent."
    }
  ],
  "Resolve": [
    {
      "skill": "Confidence",
      "stat_pair": "Vitality + Willpower",
      "effect": "Passive: While at Maximum Composure, you have Advantage on all Social defense checks."
    },
    {
      "skill": "Reasoning",
      "stat_pair": "Reflexes + Awareness",
      "effect": "Passive: You may use Logic instead of Willpower when making checks to resist Horrifying Sights or fear effects."
    },
    {
      "skill": "Cavalier",
      "stat_pair": "Finesse + Charm",
      "effect": "Action: Once per encounter, taunt an attacker who misses you. They suffer 1d4 Composure damage immediately."
    }
  ],
  "Operations": [
    {
      "skill": "Alter",
      "stat_pair": "Might + Logic",
      "effect": "Passive: Advantage on all checks made to destroy cover, breach doors, or dynamically create Difficult Terrain."
    },
    {
      "skill": "Utilize",
      "stat_pair": "Fortitude + Logic",
      "effect": "Action: Once per encounter, interact with the environment (throw sand, drop a chandelier) to gain Advantage on your next action."
    },
    {
      "skill": "Introduce",
      "stat_pair": "Endurance + Awareness",
      "effect": "Action: Once per cycle, grant an ally within 30ft +2 to their Natural Defense for 1 round by calling out incoming threats."
    }
  ],
  "Tactics": [
    {
      "skill": "Command",
      "stat_pair": "Fortitude + Charm",
      "effect": "Action: Once per cycle, command an ally. They may instantly swap their active reserved Loadout points without penalty."
    },
    {
      "skill": "Exploit",
      "stat_pair": "Reflexes + Intuition",
      "effect": "Action: Once per encounter, if an enemy becomes Staggered, you may instantly jump your turn order to act immediately after them."
    },
    {
      "skill": "Tactics",
      "stat_pair": "Reflexes + Charm",
      "effect": "Passive: If you act first in the Initiative order, all allies gain +5ft Move Speed for the duration of the first round."
    }
  ],
  "Stabilize": [
    {
      "skill": "First Aid",
      "stat_pair": "Endurance + Intuition",
      "effect": "Action: Once per encounter, you may attempt to stabilize a dying ally or stitch a wound as a Bonus Action instead of a Main Action."
    },
    {
      "skill": "Medicine",
      "stat_pair": "Vitality + Knowledge",
      "effect": "Passive: Advantage on all checks to cure, resist, or remove Bleeding, Poison, or Disease statuses."
    },
    {
      "skill": "Surgery",
      "stat_pair": "Fortitude + Intuition",
      "effect": "Passive: During a Rest Cycle, you have Advantage on checks to heal Severe Body Injuries and remove scars."
    }
  ],
  "Rally": [
    {
      "skill": "Self-Awareness",
      "stat_pair": "Finesse + Willpower",
      "effect": "Action: Once per cycle, automatically succeed on a check to resist a Mental Fracture or Trauma."
    },
    {
      "skill": "Detached",
      "stat_pair": "Endurance + Knowledge",
      "effect": "Passive: You do not suffer the standard Disadvantage penalties when your Composure drops below 50%."
    },
    {
      "skill": "Mindfulness",
      "stat_pair": "Awareness + Finesse",
      "effect": "Action: Once per encounter, perform a Rally action (healing Composure) on an ally at up to 15ft range instead of touch."
    }
  ],
  "Mobility": [
    {
      "skill": "Charge",
      "stat_pair": "Reflexes + Willpower",
      "effect": "Passive: If you move at least 15ft in a straight line towards an enemy, gain Advantage on your next Melee Attack check against them."
    },
    {
      "skill": "Flanking",
      "stat_pair": "Vitality + Awareness",
      "effect": "Passive: You do not provoke Free Attacks (Attacks of Opportunity) when moving out of or around an enemy's reach."
    },
    {
      "skill": "Speed",
      "stat_pair": "Finesse + Knowledge",
      "effect": "Passive: If you take a Move Action on two consecutive turns, your base Speed increases by +10ft for the rest of the encounter."
    }
  ],
  "Bravery": [
    {
      "skill": "Commitment",
      "stat_pair": "Might + Charm",
      "effect": "Passive: You have Advantage on all Composure and Resolve checks while standing adjacent to an enemy."
    },
    {
      "skill": "Determined",
      "stat_pair": "Might + Willpower",
      "effect": "Passive: Allies starting their turn within Line of Sight and moving directly toward you gain +5ft Move Speed."
    },
    {
      "skill": "Outsmart",
      "stat_pair": "Vitality + Logic",
      "effect": "Action: Once per encounter, smoothly Retreat from an engagement. You gain Advantage on your next Initiative check."
    }
  ]
}

os.makedirs("data", exist_ok=True)
os.makedirs("saga_vtt_client/src/data", exist_ok=True)

with open("data/tactical_triads.json", "w") as f:
    json.dump(tactical_triads, f, indent=2)

with open("saga_vtt_client/src/data/tactical_triads.json", "w") as f2:
    json.dump(tactical_triads, f2, indent=2)

print("Tactical Triads successfully balanced and regenerated.")
