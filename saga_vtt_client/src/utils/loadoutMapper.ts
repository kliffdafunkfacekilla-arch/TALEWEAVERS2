import type { LoadoutItem } from '../store/useGameStore';
import type { CharacterSheet } from '../store/useCharacterStore';
import tacticalTriadsData from '../data/tactical_triads.json';
import schoolsOfPowerData from '../data/schools_of_power.json';

// Fallback registry for weapons and items since Item Foundry is server-side
const MOCK_ITEMS: Record<string, Partial<LoadoutItem>> = {
    'wpn_rusted_cleaver': { name: 'Rusted Cleaver', type: 'MELEE', target: 'ADJACENT', range: 1, stamina_cost: 2, dice: '1d6+STR', desc: 'A heavy, oxidized blade.' },
    'wpn_steel_rapier': { name: 'Steel Rapier', type: 'MELEE', target: 'ADJACENT', range: 1, stamina_cost: 1, dice: '1d8', desc: 'A swift, elegant thrust.' },
    'wpn_hunting_bow': { name: 'Hunting Bow', type: 'RANGED', target: 'LINE_OF_SIGHT', range: 6, stamina_cost: 1, dice: '1d8', desc: 'Standard issue ranged weapon.' },
    'csm_travelers_bread': { name: 'Traveler\'s Bread', type: 'CONSUMABLE', target: 'SELF', range: 0, stamina_cost: 0, dice: '+STM', desc: 'Restores stamina.' },
    'csm_stamina_tea': { name: 'Stamina Tea', type: 'CONSUMABLE', target: 'SELF', range: 0, stamina_cost: 0, dice: '+STM', desc: 'A bitter brew.' },
    'csm_ddust': { name: 'D-Dust Vials', type: 'CONSUMABLE', target: 'SELF', range: 0, stamina_cost: 0, dice: '+FOC', desc: 'Raw magical fuel.' }
};

export function generateLoadoutFromSheet(sheet: CharacterSheet): LoadoutItem[] {
    const deck: LoadoutItem[] = [];

    // 1. Process Equipped Items
    if (sheet.loadout) {
        Object.values(sheet.loadout).forEach(itemId => {
            const itemDef = MOCK_ITEMS[itemId];
            if (itemDef) {
                deck.push({
                    id: itemId,
                    name: itemDef.name || 'Unknown Item',
                    type: itemDef.type as any || 'CONSUMABLE',
                    target: itemDef.target || 'SELF',
                    range: itemDef.range || 0,
                    stamina_cost: itemDef.stamina_cost || 0,
                    dice: itemDef.dice || '1d4',
                    desc: itemDef.desc || ''
                });
            }
        });
    } else if ((sheet as any).equipped_loadout) {
        // Fallback for older sheet structures
        Object.values((sheet as any).equipped_loadout).forEach((itemId: any) => {
            const itemDef = MOCK_ITEMS[itemId as string];
            if (itemDef) {
                deck.push({
                    id: itemId,
                    name: itemDef.name || 'Unknown Item',
                    type: itemDef.type as any || 'CONSUMABLE',
                    target: itemDef.target || 'SELF',
                    range: itemDef.range || 0,
                    stamina_cost: itemDef.stamina_cost || 0,
                    dice: itemDef.dice || '1d4',
                    desc: itemDef.desc || ''
                });
            }
        });
    }

    // 2. Process Tactical Skills
    if (sheet.tactical_skills) {
        Object.entries(sheet.tactical_skills).forEach(([skillName, skillData]: [string, any]) => {
            const rank = typeof skillData === 'object' ? skillData.rank : skillData;

            // Re-capitalize to match JSON keys like "Assault", "Mobility"
            const queryName = skillName.charAt(0).toUpperCase() + skillName.slice(1).toLowerCase();
            const triadData = Object.values(tacticalTriadsData).find((t: any) => t.skill === queryName) as any;

            let desc = "A tactical maneuver.";
            let lead_stat = "might";
            let trail_stat = "endurance";

            if (triadData) {
                // Parse stats like "MIGHT / ENDURANCE"
                const stats = triadData.stat_pair.split(" / ");
                lead_stat = stats[0].toLowerCase();
                trail_stat = stats[1].toLowerCase();

                // Get Tier 1 Passive description
                if (triadData.progression && triadData.progression["1"] && triadData.progression["1"].passive) {
                    desc = triadData.progression["1"].passive.effect;
                }
            }

            // Map skill names to generic card types
            let type: any = 'UTILITY';
            if (['Assault', 'Ballistics', 'Fortify'].includes(queryName)) type = 'MELEE';
            if (['Mobility', 'Stealth', 'Thievery'].includes(queryName)) type = 'MOBILITY';
            if (['Deceive', 'Coercion', 'Diplomacy'].includes(queryName)) type = 'SOCIAL';

            deck.push({
                id: `sk_${queryName.toLowerCase()}`,
                name: queryName,
                type: type,
                target: type === 'MELEE' ? 'ADJACENT' : 'SELF',
                range: type === 'MELEE' ? 1 : 0,
                stamina_cost: 2, // Default skill cost
                desc: desc,
                lead_stat: lead_stat,
                trail_stat: trail_stat,
                skill_rank: rank,
                target_dc: 15 // Default DC
            });
        });
    }

    // 3. Process Magic Spells
    if (sheet.powers && Array.isArray(sheet.powers)) {
        sheet.powers.forEach(spellName => {
            let spellObj: any = null;
            let schoolName = "";

            // Search through the nested talent trees for the exact spell name
            for (const school of Object.values(schoolsOfPowerData)) {
                if ((school as any).tiers) {
                    for (const tierData of Object.values((school as any).tiers)) {
                        for (const choiceType of ["OFFENSE", "DEFENSE", "UTILITY"]) {
                            const power = (tierData as any)[choiceType];
                            if (power && power.name === spellName) {
                                spellObj = power;
                                schoolName = (school as any).school;
                                break;
                            }
                        }
                        if (spellObj) break;
                    }
                }
                if (spellObj) break;
            }

            if (spellObj) {
                // Parse cost strings like "2 Focus" or "1 Stamina"
                let staminaCost = 0;
                let focusCost = 0;
                const costStr = (spellObj.cost || "").toLowerCase();

                if (costStr.includes("stamina")) {
                    const match = costStr.match(/(\d+)/);
                    if (match) staminaCost = parseInt(match[0]);
                } else if (costStr.includes("focus")) {
                    const match = costStr.match(/(\d+)/);
                    if (match) focusCost = parseInt(match[0]);
                }

                deck.push({
                    id: `sp_${spellName.replace(/\s+/g, '_').toLowerCase()}`,
                    name: spellName,
                    type: 'MAGIC',
                    target: 'LINE_OF_SIGHT',
                    range: 5, // Default magic range
                    stamina_cost: staminaCost,
                    focus_cost: focusCost,
                    dice: `[${schoolName}]`,
                    desc: spellObj.effect || "A supernatural force."
                });
            } else {
                // Fallback if spell not found in current JSON
                deck.push({
                    id: `sp_fallback_${spellName.replace(/\s+/g, '_')}`,
                    name: spellName,
                    type: 'MAGIC',
                    target: 'LINE_OF_SIGHT',
                    range: 5,
                    focus_cost: 2,
                    dice: '[MAGIC]',
                    desc: "An unknown power."
                });
            }
        });
    }

    return deck;
}
