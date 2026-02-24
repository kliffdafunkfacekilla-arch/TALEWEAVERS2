import { useGameStore } from '../../store/useGameStore';

const PHYSICAL_STATS = [
    { key: 'might', label: 'Might', color: 'bg-red-600' },
    { key: 'endurance', label: 'Endurance', color: 'bg-red-700' },
    { key: 'vitality', label: 'Vitality', color: 'bg-orange-600' },
    { key: 'fortitude', label: 'Fortitude', color: 'bg-orange-700' },
    { key: 'reflexes', label: 'Reflexes', color: 'bg-amber-600' },
    { key: 'finesse', label: 'Finesse', color: 'bg-amber-700' },
] as const;

const MENTAL_STATS = [
    { key: 'knowledge', label: 'Knowledge', color: 'bg-blue-600' },
    { key: 'logic', label: 'Logic', color: 'bg-blue-700' },
    { key: 'charm', label: 'Charm', color: 'bg-violet-600' },
    { key: 'willpower', label: 'Willpower', color: 'bg-violet-700' },
    { key: 'awareness', label: 'Awareness', color: 'bg-cyan-600' },
    { key: 'intuition', label: 'Intuition', color: 'bg-cyan-700' },
] as const;

const MAX_STAT = 12;

interface StatRowProps {
    label: string;
    value: number;
    color: string;
}

function StatRow({ label, value, color }: StatRowProps) {
    const pct = Math.min((value / MAX_STAT) * 100, 100);

    return (
        <div className="flex items-center gap-3 group">
            <span className="text-xs text-zinc-400 font-medium w-20 text-right uppercase tracking-wider group-hover:text-zinc-200 transition-colors">
                {label}
            </span>
            <div className="flex-grow h-3 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
                <div
                    className={`h-full ${color} rounded-full transition-all duration-500`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <span className="text-sm font-bold text-zinc-300 w-6 text-right tabular-nums">
                {value}
            </span>
        </div>
    );
}

export function BioMatrix() {
    const attributes = useGameStore((s) => s.attributes);
    const characterName = useGameStore((s) => s.characterName);

    return (
        <div className="space-y-5">
            {/* Header */}
            <div className="text-center border-b border-zinc-800 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">Bio-Matrix</h2>
                <p className="text-lg font-semibold text-zinc-200 mt-1 font-outfit">{characterName}</p>
            </div>

            {/* Sector I: Physical */}
            <div>
                <h3 className="text-[10px] font-bold uppercase tracking-[0.25em] text-red-500/80 mb-2 pl-1">
                    ◆ Sector I — Physical
                </h3>
                <div className="space-y-1.5">
                    {PHYSICAL_STATS.map((stat) => (
                        <StatRow
                            key={stat.key}
                            label={stat.label}
                            value={attributes[stat.key]}
                            color={stat.color}
                        />
                    ))}
                </div>
            </div>

            {/* Sector II: Mental */}
            <div>
                <h3 className="text-[10px] font-bold uppercase tracking-[0.25em] text-blue-500/80 mb-2 pl-1">
                    ◆ Sector II — Mental
                </h3>
                <div className="space-y-1.5">
                    {MENTAL_STATS.map((stat) => (
                        <StatRow
                            key={stat.key}
                            label={stat.label}
                            value={attributes[stat.key]}
                            color={stat.color}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
