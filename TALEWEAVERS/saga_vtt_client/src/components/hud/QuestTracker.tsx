import { useGameStore } from '../../store/useGameStore';

export function QuestTracker() {
    const quests = useGameStore((s) => s.quests);
    const toggleQuestComplete = useGameStore((s) => s.toggleQuestComplete);

    if (quests.length === 0) return null;

    return (
        <div className="pointer-events-auto bg-zinc-950/70 backdrop-blur-md border border-zinc-800/60 rounded-xl px-4 py-3 min-w-56 shadow-2xl">
            {/* Header */}
            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-500/80 mb-2.5 flex items-center gap-1.5">
                <span className="text-sm">📜</span> Active Quests
            </h3>

            {/* Quest Items */}
            <div className="space-y-1.5">
                {quests.map((quest) => (
                    <div
                        key={quest.id}
                        onClick={() => toggleQuestComplete(quest.id)}
                        className="flex items-center gap-2.5 cursor-pointer group"
                    >
                        {/* Checkbox */}
                        <div className={`
              w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0
              transition-all duration-200
              ${quest.completed
                                ? 'bg-amber-600/30 border-amber-600'
                                : 'border-zinc-700 group-hover:border-zinc-500'
                            }
            `}>
                            {quest.completed && (
                                <span className="text-amber-400 text-[10px] font-bold">✓</span>
                            )}
                        </div>

                        {/* Quest Title */}
                        <span className={`
              text-sm transition-all duration-200
              ${quest.completed
                                ? 'text-zinc-600 line-through'
                                : 'text-zinc-300 group-hover:text-zinc-100'
                            }
            `}>
                            {quest.title}
                        </span>
                    </div>
                ))}
            </div>

            {/* Progress */}
            <div className="mt-3 pt-2 border-t border-zinc-800/50">
                <div className="flex justify-between text-[10px] text-zinc-600 tabular-nums">
                    <span className="uppercase tracking-wider">Progress</span>
                    <span className="text-amber-500/70 font-bold">
                        {quests.filter((q) => q.completed).length}/{quests.length}
                    </span>
                </div>
            </div>
        </div>
    );
}
