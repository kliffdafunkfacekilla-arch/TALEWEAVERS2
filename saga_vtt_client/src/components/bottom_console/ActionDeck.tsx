import { useState } from 'react';
import { useGameStore } from '../../store/useGameStore';
import type { LoadoutItem } from '../../store/useGameStore';

// ── Color Mappings ────────────────────────────────────────────────────
const CARD_BORDER: Record<string, string> = {
    MELEE: 'border-red-800 hover:border-red-500',
    RANGED: 'border-orange-800 hover:border-orange-500',
    MAGIC: 'border-purple-800 hover:border-purple-500',
    MOBILITY: 'border-blue-800 hover:border-blue-500',
    SOCIAL: 'border-cyan-800 hover:border-cyan-500',
    UTILITY: 'border-teal-800 hover:border-teal-500',
    CONSUMABLE: 'border-green-800 hover:border-green-500',
};

const CARD_HEADER_BG: Record<string, string> = {
    MELEE: 'bg-red-950/30',
    RANGED: 'bg-orange-950/30',
    MAGIC: 'bg-purple-950/30',
    MOBILITY: 'bg-blue-950/30',
    SOCIAL: 'bg-cyan-950/30',
    UTILITY: 'bg-teal-950/30',
    CONSUMABLE: 'bg-green-950/30',
};

const CARD_GLOW: Record<string, string> = {
    MELEE: 'bg-red-500',
    RANGED: 'bg-orange-500',
    MAGIC: 'bg-purple-500',
    MOBILITY: 'bg-blue-500',
    SOCIAL: 'bg-cyan-500',
    UTILITY: 'bg-teal-500',
    CONSUMABLE: 'bg-green-500',
};

// ── Chebyshev Distance (standard grid math for TTRPGs) ────────────
function calculateDistance(encounter: { tokens: { id: string; x: number; y: number }[] }, targetId: string): number {
    const player = encounter.tokens.find(t => t.id === 'player_1');
    const target = encounter.tokens.find(t => t.id === targetId);
    if (!player || !target) return 999;
    return Math.max(Math.abs(player.x - target.x), Math.abs(player.y - target.y));
}

export function ActionDeck() {
    const campaignId = useGameStore((s) => s.activeCampaignId);
    const uiLocked = useGameStore((s) => s.ui_locked);
    const vitals = useGameStore((s) => s.vitals);
    const activeEncounter = useGameStore((s) => s.activeEncounter);
    const selectedTargetId = useGameStore((s) => s.selectedTargetId);
    const addChatMessage = useGameStore((s) => s.addChatMessage);
    const setPlayerVitals = useGameStore((s) => s.setPlayerVitals);
    const setUiLocked = useGameStore((s) => s.setUiLocked);
    const inventorySlots = useGameStore((s) => s.inventory_slots);
    const clientLoadout = useGameStore((s) => s.clientLoadout);
    const characterSheet = useGameStore((s) => s.characterSheet);
    const addInjury = useGameStore((s) => s.addInjury);

    const [isProcessing, setIsProcessing] = useState(false);

    const handleCardClick = async (card: LoadoutItem) => {
        if (isProcessing || uiLocked) return;

        // ── Pre-flight: Stamina Check ──
        if (card.stamina_cost && vitals.stamina.current < card.stamina_cost) {
            addChatMessage({ sender: 'SYSTEM', text: `INSUFFICIENT STAMINA FOR: ${card.name}` });
            return;
        }

        // ── Pre-flight: Range Validation (skip for SELF-target cards) ──
        let targetName = 'the enemy';
        if (card.target !== 'SELF') {
            if (!selectedTargetId) {
                addChatMessage({ sender: 'SYSTEM', text: `ERROR: No target selected for ${card.name}. Click an enemy on the map.` });
                return;
            }
            if (activeEncounter) {
                const dist = calculateDistance(activeEncounter, selectedTargetId);
                if (dist > card.range) {
                    addChatMessage({ sender: 'SYSTEM', text: `OUT OF RANGE. Target is ${dist} squares away. ${card.name} max range: ${card.range}.` });
                    return;
                }
                const targetToken = activeEncounter.tokens.find(t => t.id === selectedTargetId);
                if (targetToken) targetName = targetToken.name;
            }
        }

        setIsProcessing(true);
        setUiLocked(true);

        try {
            // ══════════════════════════════════════════════════
            // BRANCH A: CONSUMABLES → Item Foundry (Port 8005)
            // ══════════════════════════════════════════════════
            if (card.type === 'CONSUMABLE') {
                addChatMessage({ sender: 'PLAYER', text: `I use ${card.name}.` });

                try {
                    const itemRes = await fetch('http://localhost:8005/items/resolve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            item_id: card.id,
                            target_vitals: {
                                current_hp: vitals.hp.current,
                                max_hp: vitals.hp.max,
                                current_stamina: vitals.stamina.current,
                                max_stamina: vitals.stamina.max,
                                current_focus: vitals.focus.current,
                                max_focus: vitals.focus.max,
                            }
                        })
                    });

                    if (!itemRes.ok) throw new Error("Item Foundry (Port 8005) offline or item ID not found.");
                    const itemData = await itemRes.json();

                    // resolve_consumable returns: { item_name, action, details, math_result, target_pool, is_unstable_triggered }
                    if (itemData.is_unstable_triggered) {
                        addChatMessage({ sender: 'SYSTEM', text: `⚠ UNSTABLE! ${itemData.details}` });
                    } else if (itemData.action === 'HEAL' && itemData.target_pool && itemData.math_result > 0) {
                        const pool = itemData.target_pool.toLowerCase();
                        const poolMap: Record<string, string> = { 'health': 'hp', 'stamina': 'stamina', 'focus': 'focus' };
                        const vitalKey = poolMap[pool] || 'hp';
                        const currentPool = vitals[vitalKey as keyof typeof vitals];
                        const newVal = Math.min(currentPool.max, currentPool.current + itemData.math_result);

                        if (vitalKey === 'hp') {
                            setPlayerVitals({ current_hp: newVal });
                        } else if (vitalKey === 'stamina') {
                            setPlayerVitals({ current_stamina: newVal });
                        } else if (vitalKey === 'focus') {
                            setPlayerVitals({ current_focus: newVal });
                        }
                        addChatMessage({ sender: 'SYSTEM', text: `ITEM: ${itemData.item_name} — ${itemData.details}` });
                    } else if (itemData.action === 'DAMAGE') {
                        addChatMessage({ sender: 'SYSTEM', text: `ITEM: ${itemData.item_name} — ${itemData.details}` });
                    } else {
                        addChatMessage({ sender: 'SYSTEM', text: `ITEM: ${itemData.item_name} — ${itemData.details || 'Effect applied.'}` });
                    }
                } catch (err) {
                    addChatMessage({ sender: 'SYSTEM', text: `[ERROR] Item Foundry offline: ${err}` });
                }

                // Also notify the Game Master for narration
                if (campaignId) {
                    try {
                        const gmRes = await fetch('http://localhost:8000/api/campaign/action', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ campaign_id: campaignId, player_input: `I consumed the ${card.name}.` })
                        });
                        const gmData = await gmRes.json();
                        if (gmData.narration) addChatMessage({ sender: 'AI_DIRECTOR', text: gmData.narration });
                    } catch {
                        // Game Master narration is non-critical
                    }
                }
            }

            // ══════════════════════════════════════════════════
            // BRANCH B: WEAPONS → Game Master (Port 8000) → Clash Engine (Port 8007)
            // ══════════════════════════════════════════════════
            else if (card.type === 'MELEE' || card.type === 'RANGED' || card.type === 'MAGIC') {
                const actionText = `I attack ${targetName} with my ${card.name}.`;
                addChatMessage({ sender: 'PLAYER', text: actionText });

                if (campaignId) {
                    try {
                        const res = await fetch('http://localhost:8000/api/campaign/action', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                campaign_id: campaignId,
                                player_input: actionText,
                                stamina_burned: card.stamina_cost
                            })
                        });

                        if (!res.ok) throw new Error("Game Master unreachable");
                        const data = await res.json();

                        if (data.system_log) addChatMessage({ sender: 'SYSTEM', text: data.system_log.trim() });
                        if (data.narration) addChatMessage({ sender: 'AI_DIRECTOR', text: data.narration });
                        if (data.updated_vitals) setPlayerVitals(data.updated_vitals);

                        // Catch injuries from the Clash Engine (attacker_injury_applied / defender_injury_applied)
                        if (data.new_injury || data.attacker_injury_applied) {
                            const injuryText = data.new_injury || data.attacker_injury_applied;
                            const track = card.type === 'MAGIC' ? 'mind' : 'body';
                            addInjury(track, injuryText);
                            addChatMessage({
                                sender: 'SYSTEM',
                                text: `[CRITICAL TRAUMA] You have sustained a permanent injury: ${injuryText.toUpperCase()}`
                            });
                        }
                    } catch (err) {
                        addChatMessage({ sender: 'SYSTEM', text: 'ERROR: Action aborted. Game Master Engine offline.' });
                    }
                } else {
                    addChatMessage({ sender: 'SYSTEM', text: `[LOCAL] Used: ${card.name} (${card.dice})` });
                }
            }

            // ══════════════════════════════════════════════════
            // BRANCH C: SKILLS → Fate Engine (Port 8006)
            // ══════════════════════════════════════════════════
            else if (card.type === 'MOBILITY' || card.type === 'SOCIAL' || card.type === 'UTILITY') {
                addChatMessage({ sender: 'PLAYER', text: `I attempt ${card.name}.` });

                try {
                    // Pull the dynamically-calculated stats from the true Character Sheet (or fallback to store attributes)
                    const attrs = characterSheet?.attributes || useGameStore.getState().attributes;
                    const leadVal = card.lead_stat ? (attrs[card.lead_stat] || 0) : 0;
                    const trailVal = card.trail_stat ? (attrs[card.trail_stat] || 0) : 0;

                    const skillRes = await fetch('http://localhost:8006/api/skills/roll', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            character_id: characterSheet?.name || "Player",
                            triad_name: `${card.lead_stat || 'unknown'} + ${card.trail_stat || 'unknown'}`,
                            lead_stat_value: leadVal,
                            trail_stat_value: trailVal,
                            skill_rank: card.skill_rank || 0,
                            target_dc: card.target_dc || 15,
                            roll_state: { is_advantage: false, is_disadvantage: false, focus_spent: 0 },
                            is_life_or_death: true
                        })
                    });

                    if (!skillRes.ok) throw new Error("Skill Engine on Port 8006 is offline.");
                    const skillData = await skillRes.json();

                    // Deduct stamina cost
                    if (card.stamina_cost > 0) {
                        const newStamina = Math.max(0, vitals.stamina.current - card.stamina_cost);
                        setPlayerVitals({ current_stamina: newStamina });
                    }

                    // Output the cold hard math
                    const resultText = skillData.is_success ? "SUCCESS" : "FAILURE";
                    let sysMsg = `[SKILL: ${card.name}] Rolled ${skillData.roll_total} (Raw 1d20: ${skillData.raw_die_face}) vs DC ${card.target_dc || 15}. ${resultText}.`;

                    // Output Scars & Stars progression triggers
                    if (skillData.scars_and_stars_trigger) {
                        sysMsg += ` >> PROGRESSION TRIGGER: ${skillData.scars_and_stars_trigger}! <<`;
                    }
                    addChatMessage({ sender: 'SYSTEM', text: sysMsg });

                    // Ask the Game Master (Port 8000) to narrate the success/failure
                    if (campaignId) {
                        try {
                            const gmRes = await fetch('http://localhost:8000/api/campaign/action', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    campaign_id: campaignId,
                                    player_input: `I attempted ${card.name}. The result was a ${resultText} with a margin of ${skillData.margin}.`
                                })
                            });
                            const gmData = await gmRes.json();
                            if (gmData.narration) addChatMessage({ sender: 'AI_DIRECTOR', text: gmData.narration });
                        } catch {
                            // Narration is non-critical
                        }
                    }
                } catch (err) {
                    addChatMessage({ sender: 'SYSTEM', text: `[ERROR] Skill Engine offline: ${err}` });

                    // Fallback: deduct stamina locally even if port 8006 is down
                    if (card.stamina_cost > 0) {
                        const newStamina = Math.max(0, vitals.stamina.current - card.stamina_cost);
                        setPlayerVitals({ current_stamina: newStamina });
                    }
                    addChatMessage({ sender: 'SYSTEM', text: `SKILL: ${card.name} activated locally. −${card.stamina_cost} Stamina.` });
                }
            }

        } catch (err) {
            addChatMessage({ sender: 'SYSTEM', text: `[ERROR] System failure: ${err}` });
        } finally {
            setIsProcessing(false);
            setUiLocked(false);
        }
    };

    const disabled = isProcessing || uiLocked;

    // Calculate current distance to target for the range indicator on cards
    const currentDist = (activeEncounter && selectedTargetId)
        ? calculateDistance(activeEncounter, selectedTargetId)
        : null;

    return (
        <div className="flex w-full h-full items-end pb-0 px-4 gap-4 relative">

            {/* Ambient glow */}
            <div className="absolute inset-0 pointer-events-none opacity-20 bg-[radial-gradient(ellipse_at_bottom,_var(--tw-gradient-stops))] from-amber-900 via-zinc-950 to-zinc-950" />

            {/* ── Action Cards ── */}
            <div className="flex-grow flex items-end justify-center gap-3 h-full">
                {clientLoadout.length === 0 && (
                    <div className="text-zinc-600 font-mono text-xs mb-8 uppercase tracking-widest">
                        [ No Items Equipped ]
                    </div>
                )}

                {clientLoadout.map((card) => {
                    // Determine if this card is in range
                    const outOfRange = card.target !== 'SELF' && currentDist !== null && currentDist > card.range;
                    // Is this a skill check card?
                    const isSkill = card.type === 'MOBILITY' || card.type === 'SOCIAL' || card.type === 'UTILITY';

                    return (
                        <button
                            key={card.id}
                            onClick={() => handleCardClick(card)}
                            disabled={disabled}
                            className={`relative group w-40 h-48 bg-zinc-900 border transition-all duration-300 ease-out transform translate-y-6 hover:translate-y-0 hover:z-10 hover:shadow-[0_-10px_20px_rgba(0,0,0,0.5)] flex flex-col text-left overflow-hidden flex-shrink-0
                                ${CARD_BORDER[card.type] || 'border-zinc-700'}
                                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                                ${outOfRange ? 'opacity-60' : ''}
                            `}
                        >
                            {/* Card Header */}
                            <div className={`p-2.5 border-b border-zinc-800 ${CARD_HEADER_BG[card.type] || 'bg-zinc-900'}`}>
                                <h4 className="text-white font-bold tracking-wider text-xs truncate uppercase">{card.name}</h4>
                                <div className="flex justify-between items-center mt-1">
                                    <span className="text-[8px] text-zinc-400 uppercase font-mono tracking-widest">{card.type}</span>
                                    <span className="text-[8px] text-zinc-500 font-mono">[{card.target}]</span>
                                </div>
                            </div>

                            {/* Card Body */}
                            <div className="p-2.5 flex-grow flex flex-col justify-between">
                                <p className="text-[10px] text-zinc-400 italic leading-relaxed">
                                    &ldquo;{card.desc}&rdquo;
                                </p>

                                <div className="space-y-1.5 mt-2">
                                    {/* Skill cards: show Lead + Trail stats */}
                                    {isSkill && card.lead_stat && card.trail_stat && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">Triad</span>
                                            <span className="text-[10px] text-cyan-400 font-mono font-bold">
                                                {card.lead_stat.slice(0, 3).toUpperCase()} + {card.trail_stat.slice(0, 3).toUpperCase()}
                                            </span>
                                        </div>
                                    )}

                                    {/* Skill cards: show DC */}
                                    {isSkill && card.target_dc && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">DC</span>
                                            <span className="text-[10px] text-amber-400 font-mono font-bold">{card.target_dc}</span>
                                        </div>
                                    )}

                                    {/* Weapon/consumable cards: show Power */}
                                    {!isSkill && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">Power</span>
                                            <span className="text-[10px] text-white font-mono font-bold">{card.dice}</span>
                                        </div>
                                    )}

                                    <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                        <span className="text-[9px] text-zinc-500 uppercase">Cost</span>
                                        <div className="flex gap-1 font-mono text-[10px] font-bold">
                                            {card.stamina_cost > 0 ? <span className="text-amber-500">{card.stamina_cost} STM</span> : <span className="text-zinc-500">FREE</span>}
                                        </div>
                                    </div>

                                    {/* Range indicator — only for non-SELF cards */}
                                    {card.target !== 'SELF' && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">Range</span>
                                            <span className={`text-[10px] font-mono font-bold ${outOfRange ? 'text-red-500' : 'text-green-500'}`}>
                                                {card.range} sq {currentDist !== null ? `(${currentDist} away)` : ''}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Out-of-range overlay */}
                            {outOfRange && (
                                <div className="absolute inset-0 bg-zinc-950/60 flex items-center justify-center pointer-events-none">
                                    <span className="text-[10px] text-red-500 font-bold uppercase tracking-widest">Out of Range</span>
                                </div>
                            )}

                            {/* Hover Glow */}
                            <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 pointer-events-none transition-opacity duration-500 ${CARD_GLOW[card.type] || 'bg-zinc-500'}`} />
                        </button>
                    );
                })}
            </div>

            {/* ── Quick Inventory (Hedge Charms) ── */}
            <div className="flex gap-2 items-end flex-shrink-0 pb-4">
                {inventorySlots.map((slot) => (
                    <div
                        key={slot.id}
                        className={`w-14 h-14 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 border-2
                            ${slot.itemName
                                ? 'bg-zinc-800 border-amber-700/50 hover:border-amber-500'
                                : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-600'
                            }
                        `}
                        title={slot.itemName || `Empty Slot ${slot.id}`}
                    >
                        {slot.itemName ? (
                            <span className="text-amber-400 text-lg">✦</span>
                        ) : (
                            <span className="text-zinc-700 text-xs">{slot.id}</span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
