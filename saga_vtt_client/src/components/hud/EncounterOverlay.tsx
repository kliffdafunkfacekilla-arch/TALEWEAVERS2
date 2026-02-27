import React from 'react';
import { useGameStore } from '../../store/useGameStore';
import { MessageSquare, Shield, AlertTriangle, Coins, X } from 'lucide-react';

export const EncounterOverlay: React.FC = () => {
    const activeEncounter = useGameStore((s) => s.activeEncounter);
    const setActiveEncounter = useGameStore((s) => s.setActiveEncounter);
    const sendAction = useGameStore((s) => s.sendAction);

    if (!activeEncounter) return null;

    const { data } = activeEncounter;
    const category = data.category || 'Encounter';

    const renderSocial = () => (
        <div className="flex flex-col gap-4">
            {data.npcs?.map((npc, idx) => (
                <div key={idx} className="bg-zinc-800/50 p-4 border border-zinc-700/50 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                        <div>
                            <h3 className="text-amber-500 font-bold uppercase tracking-wider">{npc.name}</h3>
                            <p className="text-xs text-zinc-400">{npc.species} • {npc.faction}</p>
                        </div>
                        <div className="text-right">
                            <span className="text-[10px] uppercase text-zinc-500 font-mono">Composure</span>
                            <div className="w-24 h-1.5 bg-zinc-900 rounded-full mt-1">
                                <div
                                    className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                                    style={{ width: `${(npc.composure_pool / 20) * 100}%` }}
                                />
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2 mt-4">
                        <button
                            onClick={() => sendAction('PERSUADE', 2, npc.name)}
                            className="flex-grow py-2 bg-cyan-900/30 border border-cyan-800/50 text-cyan-400 text-xs font-bold uppercase hover:bg-cyan-800/50 transition-all"
                        >
                            Persuade
                        </button>
                        <button
                            onClick={() => sendAction('INTIMIDATE', 1, npc.name)}
                            className="flex-grow py-2 bg-red-900/30 border border-red-800/50 text-red-400 text-xs font-bold uppercase hover:bg-red-800/50 transition-all"
                        >
                            Threaten
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );

    const renderDilemma = () => (
        <div className="flex flex-col gap-4">
            <p className="text-zinc-300 italic text-sm border-l-2 border-zinc-700 pl-4 py-1">
                "{data.narrative_prompt}"
            </p>
            <div className="grid grid-cols-2 gap-4 mt-2">
                {data.options?.map((opt, idx) => (
                    <button
                        key={idx}
                        onClick={() => sendAction('CHOICE', 0, opt.label)}
                        className="p-4 bg-zinc-800/30 border border-zinc-700/50 hover:border-amber-500/50 hover:bg-amber-900/10 transition-all text-left"
                    >
                        <span className="block text-amber-500 text-xs font-bold uppercase mb-1">{opt.label}</span>
                        <span className="text-[10px] text-zinc-500 leading-tight block">{opt.consequence_narrative}</span>
                    </button>
                ))}
            </div>
        </div>
    );

    const renderHazard = () => (
        <div className="bg-red-900/10 border border-red-900/30 p-4 rounded-lg">
            <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="text-red-500 w-5 h-5" />
                <h3 className="text-red-400 font-bold uppercase tracking-widest text-sm">Active Hazard: {data.title}</h3>
            </div>
            <div className="flex gap-3">
                <button
                    onClick={() => sendAction('DISARM', 2, data.title)}
                    className="flex-grow py-3 bg-red-600 border border-red-500 text-white text-xs font-bold uppercase hover:bg-red-500 transition-all shadow-[0_0_15px_rgba(220,38,38,0.3)]"
                >
                    Disarm Trap
                </button>
                <button
                    onClick={() => sendAction('EVADE', 1, data.title)}
                    className="flex-grow py-3 bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-bold uppercase hover:bg-zinc-700 transition-all"
                >
                    Brace / Dodge
                </button>
            </div>
        </div>
    );

    return (
        <div className="absolute inset-x-0 top-20 flex justify-center z-50 pointer-events-none">
            <div className="w-full max-w-xl mx-4 bg-zinc-950/80 backdrop-blur-xl border border-zinc-800 shadow-2xl rounded-xl overflow-hidden pointer-events-auto animate-in fade-in slide-in-from-top-4 duration-500">
                {/* Header */}
                <div className="bg-zinc-900/50 px-6 py-3 border-b border-zinc-800 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        {category === 'COMBAT' && <Shield className="w-4 h-4 text-red-500" />}
                        {category === 'SOCIAL' && <MessageSquare className="w-4 h-4 text-cyan-500" />}
                        {category === 'HAZARD' && <AlertTriangle className="w-4 h-4 text-red-500" />}
                        {category === 'DILEMMA' && <Coins className="w-4 h-4 text-amber-500" />}
                        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">{category}</span>
                    </div>
                    <button
                        onClick={() => setActiveEncounter(null)}
                        className="text-zinc-600 hover:text-zinc-400 transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    <h2 className="text-xl font-bold text-white mb-2 tracking-tight">{data.title}</h2>
                    <p className="text-zinc-400 text-sm mb-6 leading-relaxed">
                        {data.narrative_prompt}
                    </p>

                    {category === 'SOCIAL' && renderSocial()}
                    {category === 'DILEMMA' && renderDilemma()}
                    {category === 'HAZARD' && renderHazard()}
                </div>

                {/* Footer status */}
                <div className="px-6 py-2 bg-zinc-900/30 border-t border-zinc-800/50">
                    <p className="text-[9px] uppercase tracking-widest text-zinc-600 font-mono">
                        Awaiting Resolution...
                    </p>
                </div>
            </div>
        </div>
    );
};
