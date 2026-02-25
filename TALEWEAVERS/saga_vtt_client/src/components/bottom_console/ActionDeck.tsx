import { useState } from 'react';
import { useGameStore } from '../../store/useGameStore';

// ── Card Type ─────────────────────────────────────────────────────────
interface ActionCard {
    id: string;
    name: string;
    type: 'MELEE' | 'MOBILITY' | 'MAGIC' | 'CONSUMABLE';
    target: string;
    range: number;
    cost: { stamina?: number; hp?: number };
    dice: string;
    desc: string;
}

// Mock Card Data (In production, Module 3: Character Engine provides this)
const MOCK_DECK: ActionCard[] = [
    { id: 'act_1', name: 'Rusted Cleaver', type: 'MELEE', target: 'ADJACENT', range: 1, cost: { stamina: 1 }, dice: '1d8+2', desc: 'A heavy, brutal swing.' },
    { id: 'act_2', name: 'Snap Dodge', type: 'MOBILITY', target: 'SELF', range: 0, cost: { stamina: 2 }, dice: 'None', desc: 'Evade an incoming blow.' },
    { id: 'act_3', name: 'Hedge Charm', type: 'MAGIC', target: 'RANGED', range: 6, cost: { stamina: 1, hp: 1 }, dice: '1d6', desc: 'Burn blood to cast a hex.' },
    { id: 'act_4', name: 'D-Dust Stim', type: 'CONSUMABLE', target: 'SELF', range: 0, cost: {}, dice: '+5 HP', desc: 'Heal minor integrity.' }
];

// ── Color Mappings ────────────────────────────────────────────────────
const CARD_BORDER: Record<string, string> = {
    MELEE: 'border-red-800 hover:border-red-500',
    MAGIC: 'border-purple-800 hover:border-purple-500',
    MOBILITY: 'border-blue-800 hover:border-blue-500',
    CONSUMABLE: 'border-green-800 hover:border-green-500',
};

const CARD_HEADER_BG: Record<string, string> = {
    MELEE: 'bg-red-950/30',
    MAGIC: 'bg-purple-950/30',
    MOBILITY: 'bg-blue-950/30',
    CONSUMABLE: 'bg-green-950/30',
};

const CARD_GLOW: Record<string, string> = {
    MELEE: 'bg-red-500',
    MAGIC: 'bg-purple-500',
    MOBILITY: 'bg-blue-500',
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

    const [isProcessing, setIsProcessing] = useState(false);

    const handleCardClick = async (card: ActionCard) => {
        if (isProcessing || uiLocked) return;

        // ── Pre-flight: Stamina Check ──
        if (card.cost.stamina && vitals.stamina.current < card.cost.stamina) {
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

        const actionText = card.target === 'SELF'
            ? `I use ${card.name}.`
            : `I attack ${targetName} with my ${card.name}.`;

        addChatMessage({ sender: 'PLAYER', text: actionText });

        if (campaignId) {
            try {
                const res = await fetch('http://localhost:8000/api/campaign/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ campaign_id: campaignId, player_input: actionText })
                });

                if (!res.ok) throw new Error("Game Master unreachable");
                const data = await res.json();

                if (data.system_log) addChatMessage({ sender: 'SYSTEM', text: data.system_log.trim() });
                if (data.narration) addChatMessage({ sender: 'AI_DIRECTOR', text: data.narration });
                if (data.updated_vitals) setPlayerVitals(data.updated_vitals);
            } catch (err) {
                addChatMessage({ sender: 'SYSTEM', text: 'ERROR: Action aborted. Game Master Engine offline.' });
            }
        } else {
            addChatMessage({ sender: 'SYSTEM', text: `[LOCAL] Used: ${card.name} (${card.dice})` });
        }

        setIsProcessing(false);
        setUiLocked(false);
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
                {MOCK_DECK.map((card) => {
                    // Determine if this card is in range
                    const outOfRange = card.target !== 'SELF' && currentDist !== null && currentDist > card.range;

                    return (
                        <button
                            key={card.id}
                            onClick={() => handleCardClick(card)}
                            disabled={disabled}
                            className={`relative group w-40 h-48 bg-zinc-900 border transition-all duration-300 ease-out transform translate-y-6 hover:translate-y-0 hover:z-10 hover:shadow-[0_-10px_20px_rgba(0,0,0,0.5)] flex flex-col text-left overflow-hidden flex-shrink-0
                                ${CARD_BORDER[card.type]}
                                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                                ${outOfRange ? 'opacity-60' : ''}
                            `}
                        >
                            {/* Card Header */}
                            <div className={`p-2.5 border-b border-zinc-800 ${CARD_HEADER_BG[card.type]}`}>
                                <h4 className="text-white font-bold tracking-wider text-xs truncate uppercase">{card.name}</h4>
                                <div className="flex justify-between items-center mt-1">
                                    <span className="text-[8px] text-zinc-400 uppercase font-mono tracking-widest">{card.type}</span>
                                    <span className="text-[8px] text-zinc-500 font-mono">[{card.target}]</span>
                                </div>
                            </div>

                            {/* Card Body */}
                            <div className="p-2.5 flex-grow flex flex-col justify-between">
                                <p className="text-[10px] text-zinc-400 italic leading-relaxed">
                                    "{card.desc}"
                                </p>

                                <div className="space-y-1.5 mt-2">
                                    <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                        <span className="text-[9px] text-zinc-500 uppercase">Power</span>
                                        <span className="text-[10px] text-white font-mono font-bold">{card.dice}</span>
                                    </div>

                                    <div className="flex justify-between items-center bg-zinc-950 p-1 px-2 border border-zinc-800">
                                        <span className="text-[9px] text-zinc-500 uppercase">Cost</span>
                                        <div className="flex gap-1 font-mono text-[10px] font-bold">
                                            {card.cost.stamina ? <span className="text-amber-500">{card.cost.stamina} STM</span> : null}
                                            {card.cost.hp ? <span className="text-red-500 ml-1">{card.cost.hp} HP</span> : null}
                                            {!card.cost.stamina && !card.cost.hp ? <span className="text-zinc-500">FREE</span> : null}
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
                            <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 pointer-events-none transition-opacity duration-500 ${CARD_GLOW[card.type]}`} />
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
