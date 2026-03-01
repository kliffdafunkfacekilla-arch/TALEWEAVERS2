import React from 'react';
import { useGameStore } from '../../store/useGameStore';
import { useCharacterStore } from '../../store/useCharacterStore';
import { useCombatStore } from '../../store/useCombatStore';
import { Sword, Target, Crosshair, Hexagon } from 'lucide-react';

export const ActionHUD: React.FC = () => {
    const skills = useCharacterStore(s => s.skills);
    const selectedTargetId = useCombatStore(s => s.selectedTargetId);
    const activeEncounter = useCombatStore(s => s.activeEncounter);
    const executeAction = useGameStore(s => s.executeAction);
    const ui_locked = useGameStore(s => s.ui_locked);

    // If there is no battlemap rendering, do not show the tactical HUD
    if (!activeEncounter) return null;

    const handleSkillClick = async (skill: string, targetId: string) => {
        try {
            console.log(`[ActionHUD] Requesting skill execution: ${skill} against ${targetId}`);
            await executeAction(skill, targetId);
        } catch (error: any) {
            console.error("[ActionHUD ERRROR] Fatality:", error);
            alert(`[ActionHUD Crash] ${error.message || error}`);
        }
    };

    return (
        <div className="absolute inset-x-0 bottom-8 flex justify-center z-40 pointer-events-none">
            <div className="bg-zinc-950/90 backdrop-blur-md border outline outline-1 outline-black/50 border-zinc-700 p-2 rounded-xl flex gap-1 shadow-[0_20px_50px_rgba(0,0,0,0.8)] pointer-events-auto">
                <div className="flex border-r border-zinc-800 pr-2 mr-1 gap-1">
                    <button
                        onClick={() => selectedTargetId && handleSkillClick("Basic Attack", selectedTargetId)}
                        disabled={!selectedTargetId || ui_locked}
                        className={`w-12 h-12 bg-zinc-900 border transition-colors flex items-center justify-center rounded-lg group relative
                            ${!selectedTargetId || ui_locked ? 'border-zinc-800 text-zinc-700' : 'border-zinc-700 hover:border-zinc-400 text-zinc-500 hover:text-white hover:bg-zinc-800'}
                        `}
                    >
                        <Sword className="w-5 h-5" />
                        <span className="absolute -top-8 bg-black border border-zinc-800 text-[10px] font-bold text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest whitespace-nowrap">Basic Attack</span>
                    </button>
                    <button
                        onClick={() => selectedTargetId && handleSkillClick("Ranged Attack", selectedTargetId)}
                        disabled={!selectedTargetId || ui_locked}
                        className={`w-12 h-12 bg-zinc-900 border transition-colors flex items-center justify-center rounded-lg group relative
                            ${!selectedTargetId || ui_locked ? 'border-zinc-800 text-zinc-700' : 'border-zinc-700 hover:border-zinc-400 text-zinc-500 hover:text-white hover:bg-zinc-800'}
                        `}
                    >
                        <Crosshair className="w-5 h-5" />
                        <span className="absolute -top-8 bg-black border border-zinc-800 text-[10px] font-bold text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest whitespace-nowrap">Ranged Attack</span>
                    </button>
                </div>

                {/* Player Traits/Skills */}
                <div className="flex gap-1">
                    {skills.map((skill, idx) => (
                        <button
                            key={idx}
                            disabled={!selectedTargetId || ui_locked}
                            onClick={() => selectedTargetId && handleSkillClick(skill, selectedTargetId)}
                            className={`w-12 h-12 flex items-center justify-center rounded-lg text-xs font-bold transition-all relative group
                                ${ui_locked ? 'bg-zinc-900 border border-zinc-800 text-zinc-700' :
                                    selectedTargetId ? 'bg-amber-900/20 border border-amber-900/50 hover:bg-amber-900/40 hover:border-amber-500 text-amber-500' :
                                        'bg-zinc-900 border border-zinc-700 text-zinc-500'}
                            `}
                        >
                            <Hexagon className="w-6 h-6 absolute opacity-20" />
                            <span className="z-10 text-[9px] uppercase max-w-[40px] leading-tight text-center break-words">{skill.split(' ')[0]}</span>

                            <span className="absolute -top-8 bg-black border border-amber-900/50 text-[10px] font-bold text-amber-500 px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest whitespace-nowrap">
                                Use {skill}
                            </span>
                        </button>
                    ))}
                </div>

                <div className="flex border-l border-zinc-800 pl-2 ml-1 gap-1">
                    <button
                        className={`w-12 h-12 flex items-center justify-center rounded-lg transition-colors group relative
                            ${selectedTargetId ? 'bg-red-900/20 border border-red-900/50 text-red-500' : 'bg-zinc-900 border border-zinc-700 text-zinc-600'}
                        `}
                    >
                        <Target className={`w-5 h-5 ${selectedTargetId ? 'animate-pulse' : ''}`} />
                        <span className={`absolute -top-8 bg-black border text-[10px] font-bold text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest whitespace-nowrap
                            ${selectedTargetId ? 'border-red-900 text-red-500' : 'border-zinc-800'}
                        `}>
                            {selectedTargetId ? 'Enemy Targeted' : 'No Target'}
                        </span>
                    </button>
                </div>
            </div>
        </div>
    );
};
