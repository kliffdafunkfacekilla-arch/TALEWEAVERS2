import { useState } from 'react';
import { useGameStore } from '../../store/useGameStore';

export function ActionDeck() {
    const skills = useGameStore((s) => s.skills);
    const uiLocked = useGameStore((s) => s.ui_locked);
    const stamina = useGameStore((s) => s.vitals.stamina);
    const selectedTokenId = useGameStore((s) => s.selectedTokenId);
    const sendAction = useGameStore((s) => s.sendAction);
    const inventorySlots = useGameStore((s) => s.inventory_slots);
    const [burnAmount, setBurnAmount] = useState(0);

    const handleSkillClick = (skill: string) => {
        if (uiLocked) return;
        const target = selectedTokenId || 'NONE';
        sendAction(skill, burnAmount, target);
        setBurnAmount(0);
    };

    return (
        <div className="flex w-full max-w-7xl h-full items-end pb-4 px-6 gap-8">

            {/* CENTER: Skills & Burn Slider */}
            <div className="flex-grow flex flex-col justify-end gap-3">
                {/* Tactical Grit Burn Slider */}
                <div className="flex items-center gap-4 bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/80 backdrop-blur-sm">
                    <span className="text-zinc-500 text-xs uppercase font-bold tracking-wider whitespace-nowrap">
                        Burn Stamina
                    </span>
                    <input
                        type="range"
                        min="0"
                        max={stamina.current}
                        value={burnAmount}
                        onChange={(e) => setBurnAmount(Number(e.target.value))}
                        disabled={uiLocked}
                        className="flex-grow accent-red-500 h-2 disabled:opacity-40"
                    />
                    <span className={`font-bold text-lg tabular-nums min-w-[3ch] text-right ${burnAmount > 0 ? 'text-red-400' : 'text-zinc-600'
                        }`}>
                        +{burnAmount}
                    </span>
                </div>

                {/* Skill Buttons */}
                <div className="flex justify-center gap-2 flex-wrap">
                    {skills.map((skill) => (
                        <button
                            key={skill}
                            onClick={() => handleSkillClick(skill)}
                            disabled={uiLocked}
                            className={`
                px-5 py-3 rounded-lg text-sm font-bold uppercase tracking-wider
                transition-all duration-200 border-b-4
                ${uiLocked
                                    ? 'bg-zinc-900 border-zinc-950 text-zinc-700 cursor-not-allowed'
                                    : 'bg-zinc-800 border-zinc-950 text-zinc-200 hover:bg-red-900/80 hover:border-red-950 hover:text-white hover:shadow-lg hover:shadow-red-900/20 active:translate-y-0.5 active:border-b-2'
                                }
              `}
                        >
                            {skill}
                        </button>
                    ))}
                </div>
            </div>

            {/* RIGHT: Quick Inventory (Hedge Charms) */}
            <div className="flex gap-2 items-end flex-shrink-0">
                {inventorySlots.map((slot) => (
                    <div
                        key={slot.id}
                        className={`
              w-14 h-14 rounded-lg flex items-center justify-center cursor-pointer
              transition-all duration-200 border-2
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
