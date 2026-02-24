import { useGameStore } from '../../store/useGameStore';

const MAX_BODY_SLOTS = 4;
const MAX_MIND_SLOTS = 4;

export function InjurySlots() {
    const injuries = useGameStore((s) => s.injuries);

    const renderSlots = (active: string[], maxSlots: number, trackColor: string, emptyLabel: string) => {
        const slots = [];
        for (let i = 0; i < maxSlots; i++) {
            const injury = active[i] || null;
            slots.push(
                <div
                    key={i}
                    className={`
            flex items-center gap-2 px-3 py-2 rounded-lg border text-sm
            transition-all duration-300
            ${injury
                            ? `${trackColor} bg-zinc-900`
                            : 'border-zinc-800/50 bg-zinc-950/50'
                        }
          `}
                >
                    <span className={`text-base ${injury ? '' : 'opacity-20'}`}>
                        {injury ? '🩸' : '○'}
                    </span>
                    <span className={injury ? 'text-zinc-200 font-medium' : 'text-zinc-700 italic text-xs'}>
                        {injury || `${emptyLabel} ${i + 1}`}
                    </span>
                </div>
            );
        }
        return slots;
    };

    return (
        <div className="space-y-4 mt-4">
            {/* Header */}
            <div className="text-center">
                <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">
                    Injury Tracks
                </h3>
            </div>

            {/* Body Track */}
            <div>
                <h4 className="text-[10px] font-bold uppercase tracking-[0.25em] text-red-500/70 mb-2 pl-1 flex items-center gap-1.5">
                    <span className="text-sm">🦴</span> Body Injuries
                </h4>
                <div className="space-y-1.5">
                    {renderSlots(injuries.body, MAX_BODY_SLOTS, 'border-red-800/60', 'Body Slot')}
                </div>
            </div>

            {/* Mind Track */}
            <div>
                <h4 className="text-[10px] font-bold uppercase tracking-[0.25em] text-violet-500/70 mb-2 pl-1 flex items-center gap-1.5">
                    <span className="text-sm">🧠</span> Mind Injuries
                </h4>
                <div className="space-y-1.5">
                    {renderSlots(injuries.mind, MAX_MIND_SLOTS, 'border-violet-800/60', 'Mind Slot')}
                </div>
            </div>

            {/* Severity Indicator */}
            <div className="pt-2 border-t border-zinc-800/50">
                <div className="flex justify-between text-[10px] text-zinc-600 uppercase tracking-wider">
                    <span>Total Wounds</span>
                    <span className={`font-bold ${injuries.body.length + injuries.mind.length > 4 ? 'text-red-400' :
                            injuries.body.length + injuries.mind.length > 0 ? 'text-amber-400' :
                                'text-emerald-400'
                        }`}>
                        {injuries.body.length + injuries.mind.length} / {MAX_BODY_SLOTS + MAX_MIND_SLOTS}
                    </span>
                </div>
            </div>
        </div>
    );
}
