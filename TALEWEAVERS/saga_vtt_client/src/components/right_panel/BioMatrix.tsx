import { useGameStore } from '../../store/useGameStore';

// ── 12 Core Attributes Display ──────────────────────────────────────
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

// ── Vitals Pool Bar ──────────────────────────────────────────────────
interface VitalBarProps {
    label: string;
    current: number;
    max: number;
    barColor: string;
    criticalColor: string;
    criticalThreshold: number;
}

function VitalBar({ label, current, max, barColor, criticalColor, criticalThreshold }: VitalBarProps) {
    const pct = Math.max(0, Math.min(100, (current / max) * 100));
    const isCritical = current <= criticalThreshold;

    return (
        <div>
            <div className="flex justify-between text-xs text-zinc-400 mb-1.5 font-bold uppercase tracking-wider">
                <span>{label}</span>
                <span className={`font-mono ${isCritical ? 'text-red-500 animate-pulse' : 'text-white'}`}>
                    {current} / {max}
                </span>
            </div>
            <div className="w-full h-4 bg-zinc-950 border border-zinc-800 overflow-hidden relative shadow-inner">
                <div
                    className={`h-full transition-all duration-700 ease-out ${isCritical ? `${criticalColor} shadow-[0_0_10px_rgba(220,38,38,0.8)]` : barColor}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    );
}

// ── Stamina Pips ──────────────────────────────────────────────────────
interface StaminaPipsProps {
    label: string;
    current: number;
    max: number;
    activeColor: string;
}

function StaminaPips({ label, current, max, activeColor }: StaminaPipsProps) {
    return (
        <div>
            <div className="flex justify-between text-xs text-zinc-400 mb-1.5 font-bold uppercase tracking-wider">
                <span>{label}</span>
                <span className="text-white font-mono">{current} / {max}</span>
            </div>
            <div className="w-full h-3 flex gap-1">
                {[...Array(max)].map((_, i) => (
                    <div
                        key={i}
                        className={`flex-1 h-full border border-zinc-900 transition-colors duration-300 ${i < current
                                ? `${activeColor} shadow-[0_0_6px_rgba(245,158,11,0.4)]`
                                : 'bg-zinc-800/50'
                            }`}
                    />
                ))}
            </div>
        </div>
    );
}

// ── Main Component ────────────────────────────────────────────────────
export function BioMatrix() {
    const attributes = useGameStore((s) => s.attributes);
    const vitals = useGameStore((s) => s.vitals);
    const characterName = useGameStore((s) => s.characterName);

    return (
        <div className="space-y-5">
            {/* Header */}
            <div className="text-center border-b border-zinc-800 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">Bio-Matrix</h2>
                <p className="text-lg font-semibold text-zinc-200 mt-1 font-outfit">{characterName}</p>
            </div>

            {/* ── Survival Pools ── */}
            <div className="space-y-3">
                <h3 className="text-[10px] font-bold uppercase tracking-[0.25em] text-red-500/80 pl-1">
                    ◆ Survival Pools
                </h3>

                <VitalBar
                    label="Integrity (HP)"
                    current={vitals.hp.current}
                    max={vitals.hp.max}
                    barColor="bg-green-600"
                    criticalColor="bg-red-600"
                    criticalThreshold={Math.floor(vitals.hp.max * 0.25)}
                />

                <StaminaPips
                    label="Stamina"
                    current={vitals.stamina.current}
                    max={vitals.stamina.max}
                    activeColor="bg-amber-500"
                />

                <VitalBar
                    label="Focus"
                    current={vitals.focus.current}
                    max={vitals.focus.max}
                    barColor="bg-blue-600"
                    criticalColor="bg-blue-900"
                    criticalThreshold={Math.floor(vitals.focus.max * 0.25)}
                />

                <VitalBar
                    label="Composure"
                    current={vitals.composure.current}
                    max={vitals.composure.max}
                    barColor="bg-violet-600"
                    criticalColor="bg-violet-900"
                    criticalThreshold={Math.floor(vitals.composure.max * 0.25)}
                />
            </div>

            {/* ── Sector I: Physical ── */}
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

            {/* ── Sector II: Mental ── */}
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
