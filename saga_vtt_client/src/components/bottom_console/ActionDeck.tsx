import { useState } from 'react';
import { useGameStore, type LoadoutItem } from '../../store/useGameStore';
import { useCharacterStore } from '../../store/useCharacterStore';
import { useCombatStore } from '../../store/useCombatStore';

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
    const addChatMessage = useGameStore((s) => s.addChatMessage);
    const setUiLocked = useGameStore((s) => s.setUiLocked);
    const inventorySlots = useGameStore((s) => s.inventory_slots);
    const clientLoadout = useGameStore((s) => s.clientLoadout);

    const vitals = useCharacterStore((s) => s.vitals);
    const setPlayerVitals = useCharacterStore((s) => s.setPlayerVitals);

    const activeEncounter = useCombatStore((s) => s.activeEncounter);
    const selectedTargetId = useCombatStore((s) => s.selectedTargetId);

    const [isProcessing, setIsProcessing] = useState(false);

    // ── Default Exploration Cards (Tier 5) ──
    const defaultExplorationCards: LoadoutItem[] = [
        {
            id: 'action_search',
            name: 'Search',
            type: 'UTILITY',
            target: 'AREA',
            range: 1,
            stamina_cost: 2,
            target_dc: 15,
            lead_stat: 'awareness',
            trail_stat: 'intuition',
            desc: 'Scour the immediate area for hidden loot, traps, or clues.'
        },
        {
            id: 'action_observe',
            name: 'Observe',
            type: 'UTILITY',
            target: 'TARGET',
            range: 5,
            stamina_cost: 1,
            target_dc: 10,
            lead_stat: 'awareness',
            trail_stat: 'logic',
            desc: 'Study a person or object to glean more information.'
        },
        {
            id: 'action_rest',
            name: 'Catch Breath',
            type: 'UTILITY',
            target: 'SELF',
            range: 0,
            stamina_cost: 0,
            desc: 'Recover 5 Stamina and 2 HP. Takes 1 Turn.'
        }
    ];

    const handleCardClick = async (card: LoadoutItem) => {
        if (isProcessing || uiLocked) return;

        // ── Pre-flight: Stamina Check ──
        if (card.stamina_cost && vitals.stamina.current < card.stamina_cost) {
            addChatMessage({ sender: 'SYSTEM', text: `INSUFFICIENT STAMINA FOR: ${card.name}` });
            return;
        }

        // ── Pre-flight: Range Validation ──
        let targetName = 'the surroundings';
        if (card.target === 'TARGET' || card.target === 'ENEMY') {
            if (!selectedTargetId) {
                addChatMessage({ sender: 'SYSTEM', text: `ERROR: No target selected for ${card.name}. Click an object or NPC on the map.` });
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
            // Handle Rest separately
            if (card.id === 'action_rest') {
                addChatMessage({ sender: 'PLAYER', text: "I take a moment to rest." });
                const directorUrl = import.meta.env.VITE_SAGA_DIRECTOR_URL || 'http://localhost:8000';
                const res = await fetch(`${directorUrl}/api/campaign/action`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ campaign_id: campaignId, player_input: "REST" })
                });
                const data = await res.json();
                if (data.updated_vitals) setPlayerVitals(data.updated_vitals);
                if (data.narration) addChatMessage({ sender: 'AI_DIRECTOR', text: data.narration });
                return;
            }

            // Normal Branch processing...
            if (card.type === 'CONSUMABLE') {
                addChatMessage({ sender: 'PLAYER', text: `I use ${card.name}.` });
                const rulesEngineUrl = import.meta.env.VITE_SAGA_RULES_ENGINE_URL || 'http://localhost:8014';
                const itemRes = await fetch(`${rulesEngineUrl}/api/rules/items/resolve`, {
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

                if (itemRes.ok) {
                    const itemData = await itemRes.json();
                    if (itemData.math_result > 0) {
                        const poolMap: Record<string, string> = { 'health': 'hp', 'stamina': 'stamina', 'focus': 'focus' };
                        const vitalKey = poolMap[itemData.target_pool?.toLowerCase() || 'health'] || 'hp';
                        if (vitalKey === 'hp') setPlayerVitals({ current_hp: Math.min(vitals.hp.max, vitals.hp.current + itemData.math_result) });
                    }
                    addChatMessage({ sender: 'SYSTEM', text: `ITEM: ${itemData.details}` });
                }
            }
            else if (card.id.startsWith('action_') || card.type === 'MELEE' || card.type === 'RANGED' || card.type === 'MAGIC') {
                const actionText = card.id.startsWith('action_')
                    ? `I attempt to ${card.name.toLowerCase()} at ${targetName}.`
                    : `I attack ${targetName} with my ${card.name}.`;

                addChatMessage({ sender: 'PLAYER', text: actionText });

                if (campaignId) {
                    const directorUrl = import.meta.env.VITE_SAGA_DIRECTOR_URL || 'http://localhost:8000';
                    const res = await fetch(`${directorUrl}/api/campaign/action`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            campaign_id: campaignId,
                            player_input: actionText,
                            stamina_burned: card.stamina_cost || 0
                        })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        if (data.system_log) addChatMessage({ sender: 'SYSTEM', text: data.system_log.trim() });
                        if (data.narration) addChatMessage({ sender: 'AI_DIRECTOR', text: data.narration });
                        if (data.updated_vitals) setPlayerVitals(data.updated_vitals);
                    }
                }
            }
            else if (card.type === 'MOBILITY' || card.type === 'SOCIAL' || card.type === 'UTILITY') {
                // Existing Skill Engine logic would go here...
            }

        } catch (err) {
            addChatMessage({ sender: 'SYSTEM', text: `[ERROR] Action failed: ${err}` });
        } finally {
            setIsProcessing(false);
            setUiLocked(false);
        }
    };

    const disabled = isProcessing || uiLocked;
    const currentDist = (activeEncounter && selectedTargetId) ? calculateDistance(activeEncounter, selectedTargetId) : null;

    // ── Render ──
    const displayLoadout = [...clientLoadout, ...defaultExplorationCards];

    return (
        <div className="flex w-full h-full items-end pb-0 px-4 gap-4 relative">
            <div className="absolute inset-0 pointer-events-none opacity-20 bg-[radial-gradient(ellipse_at_bottom,_var(--tw-gradient-stops))] from-amber-900 via-zinc-950 to-zinc-950" />

            <div className="flex-grow flex items-end justify-center gap-3 h-full">
                {displayLoadout.map((card) => {
                    const outOfRange = (card.target === 'TARGET' || card.target === 'ENEMY') && currentDist !== null && currentDist > card.range;
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
                                    <span className="text-[8px] text-zinc-500 font-mono">[{card.target || 'AREA'}]</span>
                                </div>
                            </div>

                            {/* Card Body */}
                            <div className="p-2.5 flex-grow flex flex-col justify-between">
                                <p className="text-[10px] text-zinc-400 italic leading-relaxed">
                                    &ldquo;{card.desc}&rdquo;
                                </p>

                                <div className="space-y-1.5 mt-2">
                                    {isSkill && card.lead_stat && card.trail_stat && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">Triad</span>
                                            <span className="text-[10px] text-cyan-400 font-mono font-bold">
                                                {card.lead_stat.slice(0, 3).toUpperCase()} + {card.trail_stat.slice(0, 3).toUpperCase()}
                                            </span>
                                        </div>
                                    )}

                                    {isSkill && card.target_dc && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">DC</span>
                                            <span className="text-[10px] text-amber-400 font-mono font-bold">{card.target_dc}</span>
                                        </div>
                                    )}

                                    {!isSkill && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">Power</span>
                                            <span className="text-[10px] text-white font-mono font-bold">{card.dice || '1d6'}</span>
                                        </div>
                                    )}

                                    <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                        <span className="text-[9px] text-zinc-500 uppercase">Cost</span>
                                        <div className="flex gap-1 font-mono text-[10px] font-bold text-right">
                                            {(card.stamina_cost || 0) > 0 && <span className="text-amber-500">{card.stamina_cost} STM</span>}
                                            {(card.focus_cost || 0) > 0 && <span className="text-purple-500 ml-1">{card.focus_cost} FOC</span>}
                                            {!card.stamina_cost && !card.focus_cost && <span className="text-zinc-500">FREE</span>}
                                        </div>
                                    </div>

                                    {(card.target === 'TARGET' || card.target === 'ENEMY') && (
                                        <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                            <span className="text-[9px] text-zinc-500 uppercase">Range</span>
                                            <span className={`text-[10px] font-mono font-bold ${outOfRange ? 'text-red-500' : 'text-green-500'}`}>
                                                {card.range} sq {currentDist !== null ? `(${currentDist} away)` : ''}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Hover Glow */}
                            <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 pointer-events-none transition-opacity duration-500 ${CARD_GLOW[card.type] || 'bg-zinc-500'}`} />
                        </button>
                    );
                })}
            </div>

            {/* Quick Inventory */}
            <div className="flex gap-2 items-end flex-shrink-0 pb-4">
                {inventorySlots.map((slot) => (
                    <div
                        key={slot.id}
                        className={`w-14 h-14 rounded-lg flex items-center justify-center cursor-pointer transition-all duration-200 border-2
                            ${slot.itemName ? 'bg-zinc-800 border-amber-700/50 hover:border-amber-500' : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-600'}
                        `}
                        title={slot.itemName || `Empty Slot ${slot.id}`}
                    >
                        {slot.itemName ? <span className="text-amber-400 text-lg">✦</span> : <span className="text-zinc-700 text-xs">{slot.id}</span>}
                    </div>
                ))}
            </div>
        </div>
    );
}
