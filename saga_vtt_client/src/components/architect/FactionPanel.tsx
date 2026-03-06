import React from 'react';
import { Plus, Trash2, Shield, Target, TrendingUp, Thermometer, Droplets } from 'lucide-react';

interface FactionPanelProps {
    factions: any[];
    setFactions: (factions: any[]) => void;
}

export const FactionPanel: React.FC<FactionPanelProps> = ({ factions, setFactions }) => {
    const addFaction = (category: 'NATION' | 'ORGANIZATION' | 'RELIGION') => {
        setFactions([...factions, {
            name: `New ${category.toLowerCase()}`,
            category: category,
            type: category === 'NATION' ? "Tribal" : category === 'RELIGION' ? "Church" : "Guild",
            expansion_rate: 0.5,
            aggression: 0.5,
            tech_level: 0.2,
            main_drive: "Growth",
            min_temp: 10, max_temp: 40,
            min_water: 0.5, max_water: 1.2
        }]);
    };

    const updateFaction = (idx: number, field: string, value: any) => {
        const newFactions = [...factions];
        newFactions[idx] = { ...newFactions[idx], [field]: value };
        setFactions(newFactions);
    };

    const removeFaction = (idx: number) => {
        setFactions(factions.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-red-500 mb-2 flex items-center gap-2">
                    <Shield className="w-4 h-4" /> 06. Geopolitical Stress
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the major power blocs, their ideological drives, and territorial expansion limits.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Global Factions</h3>
                    <div className="flex gap-2">
                        <button onClick={() => addFaction('NATION')} className="flex items-center gap-1.5 px-3 py-1 bg-red-500/10 border border-red-500/20 rounded-full text-[9px] font-black uppercase text-red-500 hover:bg-red-500/20 transition-colors">
                            <Plus className="w-3 h-3" /> Nation
                        </button>
                        <button onClick={() => addFaction('ORGANIZATION')} className="flex items-center gap-1.5 px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[9px] font-black uppercase text-zinc-300 hover:bg-white/10 transition-colors">
                            <Plus className="w-3 h-3" /> Org
                        </button>
                    </div>
                </div>

                <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {factions.map((f, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/40 border border-white/5 rounded-2xl hover:border-red-500/30 transition-all duration-300">
                            <div className="flex items-center gap-3 mb-4">
                                <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${f.category === 'NATION' ? 'bg-red-500/10 border-red-500/20' : 'bg-zinc-800 border-zinc-700'}`}>
                                    <Shield className={`w-4 h-4 ${f.category === 'NATION' ? 'text-red-500' : 'text-zinc-500'}`} />
                                </div>
                                <input
                                    type="text"
                                    value={f.name}
                                    onChange={e => updateFaction(i, 'name', e.target.value)}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-red-500 transition-colors"
                                    placeholder="FACTION_NAME"
                                />
                                <button onClick={() => removeFaction(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-6 mb-6">
                                {/* Aggression & Expansion */}
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span className="flex items-center gap-1"><Target className="w-3 h-3" /> Aggression</span>
                                            <span className="text-white font-mono">{(f.aggression * 100).toFixed(0)}%</span>
                                        </div>
                                        <input type="range" step="0.05" min="0" max="1" value={f.aggression} onChange={e => updateFaction(i, 'aggression', Number(e.target.value))} className="w-full h-1 bg-zinc-800 accent-red-500" />
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3" /> Expansion</span>
                                            <span className="text-white font-mono">{(f.expansion_rate * 100).toFixed(0)}%</span>
                                        </div>
                                        <input type="range" step="0.05" min="0" max="1" value={f.expansion_rate} onChange={e => updateFaction(i, 'expansion_rate', Number(e.target.value))} className="w-full h-1 bg-zinc-800 accent-red-500" />
                                    </div>
                                </div>

                                {/* Environmental Tolerance */}
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span className="flex items-center gap-1"><Thermometer className="w-3 h-3" /> Heat Range</span>
                                            <span className="text-white font-mono">{f.min_temp ?? 0}°/{f.max_temp ?? 40}°</span>
                                        </div>
                                        <div className="flex gap-2">
                                            <input type="range" min="-50" max="50" value={f.min_temp ?? 0} onChange={e => updateFaction(i, 'min_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-red-500" />
                                            <input type="range" min="0" max="100" value={f.max_temp ?? 40} onChange={e => updateFaction(i, 'max_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-red-500" />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span className="flex items-center gap-1"><Droplets className="w-3 h-3" /> Humidity</span>
                                            <span className="text-white font-mono">{f.min_water ?? 0}/{f.max_water ?? 1}</span>
                                        </div>
                                        <div className="flex gap-2">
                                            <input type="range" min="0" max="1" step="0.1" value={f.min_water ?? 0} onChange={e => updateFaction(i, 'min_water', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-blue-500" />
                                            <input type="range" min="0.5" max="2" step="0.1" value={f.max_water ?? 1} onChange={e => updateFaction(i, 'max_water', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-blue-500" />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Ideology & Drive */}
                            <div className="p-3 bg-black/40 border border-white/5 rounded-xl flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="flex flex-col gap-1">
                                        <span className="text-[8px] font-black text-zinc-600 uppercase">Main Drive</span>
                                        <select
                                            value={f.main_drive}
                                            onChange={e => updateFaction(i, 'main_drive', e.target.value)}
                                            className="bg-transparent text-[10px] font-bold text-zinc-300 outline-none"
                                        >
                                            <option value="Wealth">Wealth</option>
                                            <option value="Morale">Morale</option>
                                            <option value="Growth">Growth</option>
                                        </select>
                                    </div>
                                    <div className="w-px h-6 bg-white/5" />
                                    <div className="flex flex-col gap-1">
                                        <span className="text-[8px] font-black text-zinc-600 uppercase">Resource Target</span>
                                        <input
                                            type="text"
                                            value={f.resource_drive || ""}
                                            onChange={e => updateFaction(i, 'resource_drive', e.target.value)}
                                            placeholder="None"
                                            className="bg-transparent text-[10px] font-bold text-zinc-300 outline-none placeholder:text-zinc-800"
                                        />
                                    </div>
                                </div>
                                <div className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-[8px] font-black text-red-500 uppercase tracking-widest">
                                    {f.type}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
