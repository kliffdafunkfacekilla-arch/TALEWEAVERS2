import json
import os

tactical_triads = {
  "Striking": [
    {
      "skill": "Heavy Blows",
      "stat_pair": "Might + Knowledge",
      "ranks": {
        "1": "Passive: Advantage on damage rolls against enemies with heavy Natural Defense or Shields.",
        "2": "Action: Once per encounter, perform a Sunder attack. If successful, shatter the enemy's shield or destroy their cover.",
        "3": "Action: Once per cycle, perform an execution strike. Target must pass a Fortitude Check or immediately suffer a Critical Injury."
      }
    },
    {
      "skill": "Precision",
      "stat_pair": "Reflexes + Logic",
      "ranks": {
        "1": "Action: Once per encounter, declare a weak point. Gain Advantage on your next Attack check against that target.",
        "2": "Passive: Your unarmed and finesse weapons critical hit on a natural 19-20.",
        "3": "Action: Once per cycle, instantly sever an enemy limb or artery with a single flawless strike."
      }
    },
    {
      "skill": "Patience",
      "stat_pair": "Finesse + Intuition",
      "ranks": {
        "1": "Passive: If you took no offensive actions on your last turn, gain Advantage on your first Attack check this turn.",
        "2": "Action: Once per encounter, enter a reactive stance. Automatically counterattack the first enemy that misses you.",
        "3": "Action: Once per cycle, flawlessly parry a lethal blow and reflect 100% of the damage back onto the attacker."
      }
    }
  ],
  "Marksmanship": [
    {
      "skill": "Skirmishing",
      "stat_pair": "Reflexes + Knowledge",
      "ranks": {
        "1": "Passive: You do not suffer Disadvantage when making ranged attacks in close-quarters (within 5ft).",
        "2": "Passive: You may move up to 10ft after taking a shot without spending an Action.",
        "3": "Action: Once per cycle, fire a localized barrage. Attack all enemies within a 15ft cone simultaneously."
      }
    },
    {
      "skill": "Sniper",
      "stat_pair": "Finesse + Logic",
      "ranks": {
        "1": "Action: Once per encounter, gain Advantage on a Critical Injury Check to cripple a target's limb.",
        "2": "Passive: Ignore penalties for shooting into darkness, mist, or partial cover.",
        "3": "Action: Once per cycle, fire an unerring shot that ignores Line of Sight and passes through solid walls."
      }
    },
    {
      "skill": "Hurler",
      "stat_pair": "Might + Awareness",
      "ranks": {
        "1": "Action: Once per encounter, throw an object or weapon with such force the target must pass a Fortitude Check or be Staggered.",
        "2": "Passive: Thrown weapons deal bludgeoning damage in a 5ft radius on impact.",
        "3": "Action: Once per cycle, throw an object so hard it creates a concussive shockwave, knocking everyone within 20ft Prone."
      }
    }
  ],
  "Bulwark": [
    {
      "skill": "Rooted",
      "stat_pair": "Endurance + Logic",
      "ranks": {
        "1": "Passive: Immune to Forced Movement. Advantage on checks to resist being Disarmed.",
        "2": "Passive: Any enemy attempting to push or grapple you takes 1d4 bludgeoning damage from recoil.",
        "3": "Action: Once per cycle, become an immovable object. You cannot take damage or be moved for 1 entire round."
      }
    },
    {
      "skill": "Fluidity",
      "stat_pair": "Fortitude + Knowledge",
      "ranks": {
        "1": "Action: Once per encounter, automatically convert a Solid Hit against you into a Graze (half damage).",
        "2": "Passive: While unarmored, you may substitute your Reflexes for your Natural Defense.",
        "3": "Action: Once per cycle, flow like water to instantly escape any trap, grapple, or restraint."
      }
    },
    {
      "skill": "Duelist",
      "stat_pair": "Might + Intuition",
      "ranks": {
        "1": "Passive: Winning an opposed Clash roll grants Advantage on your next Assault action against that opponent.",
        "2": "Passive: Gain +2 Natural Defense as long as you are engaged with exactly one enemy.",
        "3": "Action: Once per cycle, challenge a foe. Neither of you can target anyone else, and nobody else can target either of you until one yields."
      }
    }
  ],
  "Vigilance": [
    {
      "skill": "Overwatch",
      "stat_pair": "Vitality + Intuition",
      "ranks": {
        "1": "Action: Once per cycle, declare a hex. Any enemy entering it must pass a Willpower Check or their movement drops to 0.",
        "2": "Passive: You may take two Free Attacks (Reactions) per turn instead of one.",
        "3": "Action: Once per cycle, instantly end the movement of any entity on the battlefield before they take their action."
      }
    },
    {
      "skill": "Imposing",
      "stat_pair": "Fortitude + Willpower",
      "ranks": {
        "1": "Passive: Enemies within 10ft of you suffer Disadvantage on Initiative rolls.",
        "2": "Action: Once per encounter, release a terrifying aura. All enemies in 15ft must step backward.",
        "3": "Action: Once per cycle, draw all aggro. Every enemy within Line of Sight must target you on their next turn."
      }
    },
    {
      "skill": "Threaten",
      "stat_pair": "Endurance + Charm",
      "ranks": {
        "1": "Action: Once per encounter, subtly threaten a target. They suffer Disadvantage on their next offensive action unless they move out of Line of Sight.",
        "2": "Passive: Advantage on all Intimidation checks to make enemies surrender.",
        "3": "Action: Once per cycle, speak a word of pure terror. Target permanently surrenders and flees the battle."
      }
    }
  ],
  "Wayfaring": [
    {
      "skill": "Agility",
      "stat_pair": "Reflexes + Willpower",
      "ranks": {
        "1": "Passive: Advantage on checks strictly related to jumping, climbing, or balancing.",
        "2": "Passive: You may jump from a standstill as if you had a running start.",
        "3": "Action: Once per cycle, traverse up to 60ft across any surface (including water or sheer walls) without falling."
      }
    },
    {
      "skill": "Ghost",
      "stat_pair": "Vitality + Awareness",
      "ranks": {
        "1": "Passive: Advantage on Stealth checks in dim light or natural environments.",
        "2": "Passive: You leave absolutely no footprints or scent trail.",
        "3": "Action: Once per cycle, turn completely invisible for 1 minute."
      }
    },
    {
      "skill": "Endurance",
      "stat_pair": "Finesse + Knowledge",
      "ranks": {
        "1": "Passive: Advantage on checks to survive extreme weather (heat, cold, rain).",
        "2": "Passive: You require half as much food, water, and sleep to survive.",
        "3": "Action: Once per cycle, push your body beyond its limits, ignoring all injuries and exhaustion for 1 hour."
      }
    }
  ],
  "Artifice": [
    {
      "skill": "Lock-and-Key",
      "stat_pair": "Might + Logic",
      "ranks": {
        "1": "Passive: You no longer need specialized tools to pick locks or disarm traps, using hairpins or wire instead.",
        "2": "Action: Once per encounter, instantly dismantle a hinge or jam a mechanical door mid-combat to create or deny a flanking route.",
        "3": "Action: Once per cycle, intuitively decode and disable an entire room's trap network or complex mechanism with a single glance."
      }
    },
    {
      "skill": "Sabotage",
      "stat_pair": "Fortitude + Logic",
      "ranks": {
        "1": "Action: Once per encounter, interact with the environment (cut a rope, drop a chandelier) to gain Advantage on your next action.",
        "2": "Passive: Advantage on checks specifically to craft crude bombs or chemical traps from local materials.",
        "3": "Action: Once per cycle, perfectly collapse a structure, bridge, or tunnel using minimal force applied to a critical stress point."
      }
    },
    {
      "skill": "Tinkering",
      "stat_pair": "Endurance + Awareness",
      "ranks": {
        "1": "Passive: Advantage on repairing broken equipment, weapons, or armor.",
        "2": "Action: Once per encounter, rapidly repair a sundered shield or broken firearm mid-combat.",
        "3": "Action: Once per cycle, cobble together a fully functional mechanism, vehicle, or firearm from scrap parts."
      }
    }
  ],
  "Physicker": [
    {
      "skill": "First Aid",
      "stat_pair": "Endurance + Intuition",
      "ranks": {
        "1": "Action: Once per encounter, you may attempt to stabilize a dying ally or stitch a wound as a Bonus Action instead of a Main Action.",
        "2": "Passive: Bandages applied by you grant the target 1d4 temporary Hit Points.",
        "3": "Action: Once per cycle, perfectly resuscitate a teammate who has recently died."
      }
    },
    {
      "skill": "Apothecary",
      "stat_pair": "Vitality + Knowledge",
      "ranks": {
        "1": "Passive: Advantage on all checks to forage for herbs, cure poisons, or brew antitoxins.",
        "2": "Passive: You are entirely immune to ingested and inhaled poisons.",
        "3": "Action: Once per cycle, brew a miraculous tonic that instantly purges all diseases, curses, and toxins from a target."
      }
    },
    {
      "skill": "Surgery",
      "stat_pair": "Fortitude + Intuition",
      "ranks": {
        "1": "Passive: During a Rest Cycle, you have Advantage on checks to heal Severe Body Injuries and remove scars.",
        "2": "Passive: You can perform surgery without specialized medical tools.",
        "3": "Action: Once per cycle, successfully reattach a severed limb or repair a crushed organ."
      }
    }
  ],
  "Lorecraft": [
    {
      "skill": "Arcana",
      "stat_pair": "Finesse + Willpower",
      "ranks": {
        "1": "Passive: Advantage on checks to identify magical effects, wards, and leylines.",
        "2": "Action: Once per encounter, determine the exact spell or school of magic an enemy is preparing before they cast it.",
        "3": "Action: Once per cycle, flawlessly decode and safely disarm a magical glyph or cursed artifact."
      }
    },
    {
      "skill": "Tracking",
      "stat_pair": "Endurance + Knowledge",
      "ranks": {
        "1": "Passive: Advantage on Survival checks to follow tracks or read unnatural signs in the wilderness.",
        "2": "Passive: You can determine the exact age and species of a track at a glance.",
        "3": "Action: Once per cycle, flawlessly reconstruct a scene in your mind just by examining the tracks, blood, and broken foliage."
      }
    },
    {
      "skill": "History",
      "stat_pair": "Awareness + Finesse",
      "ranks": {
        "1": "Passive: Advantage on checks to recall lore, lineage, architecture, and historical events.",
        "2": "Passive: You can accurately translate dead languages and runic scripts.",
        "3": "Action: Once per cycle, recall a devastatingly secret piece of lore about an enemy faction, exposing their fatal flaw."
      }
    }
  ],
  "Influence": [
    {
      "skill": "Intimidation",
      "stat_pair": "Vitality + Charm",
      "ranks": {
        "1": "Action: Once per encounter, force a target to roll a Composure Check with Disadvantage or be Frightened for 1 turn.",
        "2": "Passive: You can use Might instead of Charm when attempting to intimidate.",
        "3": "Action: Once per cycle, project such an overwhelming aura of dread that all enemies in 30ft immediately break Composure."
      }
    },
    {
      "skill": "Deception",
      "stat_pair": "Endurance + Willpower",
      "ranks": {
        "1": "Passive: Advantage on Social checks when attempting to lie, bluff, or feint.",
        "2": "Action: Once per encounter, flawlessly mimic an enemy's voice to issue a confusing or disastrous order.",
        "3": "Action: Once per cycle, weave a lie so profoundly believable that it completely shifts an NPC's core worldview."
      }
    },
    {
      "skill": "Persuasion",
      "stat_pair": "Fortitude + Awareness",
      "ranks": {
        "1": "Passive: Advantage on Social checks when negotiating, bribing, or bartering.",
        "2": "Passive: You instantly know a target's deepest desire after speaking to them for 1 minute.",
        "3": "Action: Once per cycle, talk a hostile enemy off the ledge, fully converting them into a temporary ally."
      }
    }
  ],
  "Conviction": [
    {
      "skill": "Unbreakable",
      "stat_pair": "Vitality + Willpower",
      "ranks": {
        "1": "Passive: While at Maximum Composure, you have Advantage on all defense checks.",
        "2": "Passive: You are completely immune to the Frightened and Charmed conditions.",
        "3": "Action: Once per cycle, automatically convert a lethal Mind Injury (Trauma) into a minor Graze."
      }
    },
    {
      "skill": "Reason",
      "stat_pair": "Reflexes + Awareness",
      "ranks": {
        "1": "Passive: You may use Logic instead of Willpower when making checks to resist Horrifying Sights.",
        "2": "Passive: Advantage on checks to instantly see through illusions and magical disguises.",
        "3": "Action: Once per cycle, use pure logic to shatter a magical enchantment or mind-control effect entirely."
      }
    },
    {
      "skill": "Defiance",
      "stat_pair": "Finesse + Charm",
      "ranks": {
        "1": "Action: Once per encounter, taunt an attacker who misses you. They suffer 1d4 Composure damage immediately.",
        "2": "Passive: Any psychic damage dealt to you is reflected back to the caster at half strength.",
        "3": "Action: Once per cycle, upon reaching 0 Composure, refuse to yield. Instantly regenerate 50% Composure and gain Advantage on all attacks."
      }
    }
  ],
  "Inspiration": [
    {
      "skill": "Rally",
      "stat_pair": "Might + Logic",
      "ranks": {
        "1": "Action: Once per encounter, grant an ally within 30ft +2 to their Composure Defense for 1 round.",
        "2": "Action: Once per encounter, you can Rally (heal) the Composure of all allies in 15ft simultaneously.",
        "3": "Action: Once per cycle, instantly clear all fear, trauma, and negative mental statuses from the entire party."
      }
    },
    {
      "skill": "Guidance",
      "stat_pair": "Fortitude + Logic",
      "ranks": {
        "1": "Passive: Advantage on checks to navigate or lead the party through treacherous terrain.",
        "2": "Action: Once per encounter, give an ally the 'Help' action from up to 30ft away.",
        "3": "Action: Once per cycle, grant an ally an automatic Critical Success (Natural 20) on a non-combat skill check."
      }
    },
    {
      "skill": "Empathy",
      "stat_pair": "Endurance + Awareness",
      "ranks": {
        "1": "Passive: You can sense the exact emotional state and Composure level of any creature you talk to.",
        "2": "Passive: Your soothing presence passively heals 1 Composure per hour to all resting allies.",
        "3": "Action: Once per cycle, absorb a severe Mind Injury or Trauma from an ally, taking it upon yourself instead."
      }
    }
  ],
  "Stratagem": [
    {
      "skill": "Command",
      "stat_pair": "Fortitude + Charm",
      "ranks": {
        "1": "Action: Once per cycle, command an ally. They may instantly swap their active reserved Loadout points without penalty.",
        "2": "Action: Once per encounter, grant a teammate an extra Move Action on their turn.",
        "3": "Action: Once per cycle, totally rearrange the Initiative order of the entire battlefield."
      }
    },
    {
      "skill": "Exploit",
      "stat_pair": "Reflexes + Intuition",
      "ranks": {
        "1": "Action: Once per encounter, if an enemy becomes Staggered, you may instantly jump your turn order to act immediately after them.",
        "2": "Passive: You deal 1d4 extra damage to enemies suffering from a status effect (Poison, Bleed, Prone).",
        "3": "Action: Once per cycle, instantly identify an enemy boss's specific weakness or gimmick."
      }
    },
    {
      "skill": "Formation",
      "stat_pair": "Reflexes + Charm",
      "ranks": {
        "1": "Passive: If you act first in the Initiative order, all allies gain +5ft Move Speed for the duration of the first round.",
        "2": "Passive: Allies standing adjacent to you gain +1 Natural Defense.",
        "3": "Action: Once per cycle, magically swap the physical locations of any two willing allies on the battlefield."
      }
    }
  ]
}

os.makedirs("data", exist_ok=True)
os.makedirs("saga_vtt_client/src/data", exist_ok=True)

with open("data/tactical_triads.json", "w") as f:
    json.dump(tactical_triads, f, indent=2)

with open("saga_vtt_client/src/data/tactical_triads.json", "w") as f2:
    json.dump(tactical_triads, f2, indent=2)

print("Tiered Tactical Triads successfully balanced and regenerated.")
