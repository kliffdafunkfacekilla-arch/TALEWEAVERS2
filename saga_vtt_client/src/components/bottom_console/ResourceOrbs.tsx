import { useGameStore, type ResourcePool } from '../../store/useGameStore';

interface OrbProps {
    label: string;
    pool: ResourcePool;
    colorClass: string;
    glowColor: string;
    bgFill: string;
}

function ResourceOrb({ label, pool, colorClass, glowColor, bgFill }: OrbProps) {
    const pct = pool.max > 0 ? (pool.current / pool.max) * 100 : 0;

    return (
        <div className="flex flex-col items-center gap-1.5">
            <span className={`text-xs font-bold uppercase tracking-[0.15em] ${colorClass}`}>
                {label}
            </span>
            <div
                className="w-20 h-20 rounded-full border-[3px] border-zinc-800 bg-zinc-950 relative overflow-hidden"
                style={{ boxShadow: `0 0 20px ${glowColor}` }}
            >
                {/* Liquid Fill */}
                <div
                    className="absolute bottom-0 w-full transition-all duration-700 ease-out"
                    style={{
                        height: `${pct}%`,
                        background: `linear-gradient(to top, ${bgFill}, ${bgFill}cc)`,
                    }}
                />
                {/* Center Text */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-white font-bold text-xl drop-shadow-md tabular-nums">
                        {pool.current}
                    </span>
                </div>
            </div>
            <span className="text-zinc-600 text-[10px] font-mono tabular-nums">
                {pool.current}/{pool.max}
            </span>
        </div>
    );
}

export function ResourceOrbs() {
    const vitals = useGameStore((s) => s.vitals);

    return (
        <div className="flex items-end gap-5">
            <ResourceOrb
                label="HP"
                pool={vitals.hp}
                colorClass="text-emerald-400"
                glowColor="rgba(52,211,153,0.15)"
                bgFill="#059669"
            />
            <ResourceOrb
                label="Stamina"
                pool={vitals.stamina}
                colorClass="text-red-400"
                glowColor="rgba(239,68,68,0.15)"
                bgFill="#dc2626"
            />
            <ResourceOrb
                label="Focus"
                pool={vitals.focus}
                colorClass="text-sky-400"
                glowColor="rgba(56,189,248,0.15)"
                bgFill="#0284c7"
            />
            <ResourceOrb
                label="Composure"
                pool={vitals.composure}
                colorClass="text-violet-400"
                glowColor="rgba(167,139,250,0.15)"
                bgFill="#7c3aed"
            />
        </div>
    );
}
