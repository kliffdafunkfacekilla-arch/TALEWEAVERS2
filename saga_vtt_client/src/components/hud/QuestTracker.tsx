import { useGameStore } from '../../store/useGameStore';

export function QuestTracker() {
    const quests = useGameStore((s) => s.quests);
    const weather = useGameStore((s) => s.weather);
    const tension = useGameStore((s) => s.tension);
    const chaosNumbers = useGameStore((s) => s.chaosNumbers);
    const sagaStage = useGameStore((s) => s.currentSagaStage);
    const pacing = useGameStore((s) => s.pacingProgress);
    const toggleQuestComplete = useGameStore((s) => s.toggleQuestComplete);

    return (
        <div className="pointer-events-auto space-y-3">
            {/* World State Info */}
            <div className="bg-zinc-950/70 backdrop-blur-md border border-zinc-800/60 rounded-xl px-4 py-3 min-w-64 shadow-2xl overflow-hidden relative">
                <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

                <div className="flex justify-between items-start mb-2">
                    <div>
                        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-500/80">
                            Current Journey
                        </h3>
                        <p className="text-sm font-medium text-zinc-100">{sagaStage}</p>
                    </div>
                    {/* Chaos Indicator */}
                    <div className="flex flex-col items-end">
                        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-purple-400/80">
                            Chaos
                        </h3>
                        <div className="flex gap-1 mt-0.5">
                            {chaosNumbers.map((n, i) => (
                                <span key={i} className="bg-purple-900/40 border border-purple-500/50 text-purple-200 text-[10px] font-mono px-1 rounded animate-pulse">
                                    {n}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-3">
                    <div>
                        <h4 className="text-[9px] uppercase tracking-wider text-zinc-500 mb-1">Environment</h4>
                        <p className="text-[11px] text-zinc-300 font-medium truncate">{weather}</p>
                    </div>
                    <div>
                        <h4 className="text-[9px] uppercase tracking-wider text-zinc-500 mb-1">World Tension</h4>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-500 ${tension > 70 ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'bg-amber-600'}`}
                                    style={{ width: `${Math.min(100, tension)}%` }}
                                />
                            </div>
                            <span className="text-[10px] font-mono text-zinc-400">{tension}%</span>
                        </div>
                    </div>
                </div>

                {/* Pacing Progress */}
                <div className="mt-3 pt-2 border-t border-zinc-800/40 flex justify-between items-center text-[10px]">
                    <span className="text-zinc-500 uppercase tracking-widest font-semibold">Stage Progress</span>
                    <span className="text-amber-500 font-bold tabular-nums">
                        {pacing.current} / {pacing.goal} Objectives
                    </span>
                </div>
            </div>

            {/* Quest Items */}
            {quests.length > 0 && (
                <div className="bg-zinc-950/70 backdrop-blur-md border border-zinc-800/60 rounded-xl px-4 py-3 min-w-64 shadow-2xl">
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-500/80 mb-2.5 flex items-center gap-1.5">
                        <span className="text-sm">📜</span> Objectives
                    </h3>

                    <div className="space-y-2">
                        {quests.map((quest) => (
                            <div
                                key={quest.id}
                                onClick={() => toggleQuestComplete(quest.id)}
                                className="flex items-start gap-2.5 cursor-pointer group"
                            >
                                <div className={`
                                    w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5
                                    transition-all duration-200
                                    ${quest.completed
                                        ? 'bg-cyan-600/30 border-cyan-600'
                                        : 'border-zinc-700 group-hover:border-zinc-500'
                                    }
                                `}>
                                    {quest.completed && (
                                        <span className="text-cyan-400 text-[10px] font-bold">✓</span>
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <p className={`
                                        text-[12px] leading-tight transition-all duration-200
                                        ${quest.completed
                                            ? 'text-zinc-600 line-through'
                                            : 'text-zinc-300 group-hover:text-zinc-100'
                                        }
                                    `}>
                                        {quest.title}
                                    </p>
                                    {quest.target_node_id && !quest.completed && (
                                        <p className="text-[9px] text-zinc-500 mt-0.5 flex items-center gap-1 uppercase tracking-tighter">
                                            <span className="text-amber-500/70">📍</span> Node: {quest.target_node_id}
                                        </p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
