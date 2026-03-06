import React from 'react';
import { Plus, Trash2, Ghost, Flame, TrendingUp, Info } from 'lucide-react';

interface ReligionPanelProps {
    religions: any[];
    setReligions: (religions: any[]) => void;
}

export const ReligionPanel: React.FC<ReligionPanelProps> = ({ religions, setReligions }) => {
    const addReligion = () => {
        setReligions([...religions, {
            name: "New Faith",
            deity: "Unknown Entity",
            expansion_rate: 1.0,
            core_tenets: ["Loyalty", "Sacrifice"]
        }]);
    };

    const updateReligion = (idx: number, field: string, value: any) => {
        const newReligions = [...religions];
        newReligions[idx] = { ...newReligions[idx], [field]: value };
        setReligions(newReligions);
    };

    const removeReligion = (idx: number) => {
        setReligions(religions.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-purple-400 mb-2 flex items-center gap-2">
                    <Ghost className="w-4 h-4" /> 08. Ideology & Faith
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the overarching spiritual frameworks and ideological pressures of the world.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Global Faiths</h3>
                    <button onClick={addReligion} className="flex items-center gap-1.5 px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-[9px] font-black uppercase text-purple-400 hover:bg-purple-500/20 transition-colors">
                        <Plus className="w-3 h-3" /> New Faith
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {religions.map((r, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/40 border border-white/5 rounded-2xl hover:border-purple-500/30 transition-all duration-300">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                                    <Flame className="w-4 h-4 text-purple-400" />
                                </div>
                                <input
                                    type="text"
                                    value={r.name}
                                    onChange={e => updateReligion(i, 'name', e.target.value)}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-purple-400 transition-colors"
                                    placeholder="FAITH_NAME"
                                />
                                <button onClick={() => removeReligion(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                    <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2">Deity / Focus</span>
                                    <input
                                        type="text"
                                        value={r.deity}
                                        onChange={e => updateReligion(i, 'deity', e.target.value)}
                                        className="w-full bg-transparent text-[10px] font-bold text-zinc-300 outline-none border-b border-white/5 focus:border-purple-500"
                                        placeholder="The Void, Mother Nature..."
                                    />
                                </div>
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                    <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2"><TrendingUp className="w-3 h-3" /> Influence Rate</span>
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="range" min="0.1" max="5" step="0.1"
                                            value={r.expansion_rate}
                                            onChange={e => updateReligion(i, 'expansion_rate', Number(e.target.value))}
                                            className="flex-grow h-1 bg-zinc-800 accent-purple-500"
                                        />
                                        <span className="text-[10px] font-mono text-white whitespace-nowrap">{r.expansion_rate.toFixed(1)}x</span>
                                    </div>
                                </div>
                            </div>

                            <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2"><Info className="w-3 h-3" /> Core Tenets</span>
                                <input
                                    type="text"
                                    value={r.core_tenets?.join(', ')}
                                    onChange={e => updateReligion(i, 'core_tenets', e.target.value.split(',').map(s => s.trim()))}
                                    className="w-full bg-transparent text-[10px] text-zinc-300 outline-none border-b border-white/5 focus:border-purple-500"
                                    placeholder="Sacrifice, Obedience, Valor..."
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
