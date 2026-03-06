import React from 'react';
import { Plus, Trash2, Pickaxe, Info } from 'lucide-react';

interface ResourcePanelProps {
    resources: any[];
    setResources: (resources: any[]) => void;
}

export const ResourcePanel: React.FC<ResourcePanelProps> = ({ resources, setResources }) => {
    const addResource = (type: 'NATURAL' | 'PRODUCED') => {
        setResources([...resources, {
            name: "New Resource",
            scarcity: 0.5,
            is_infinite: false,
            type: type,
            sources: [],
            precursor_resource: "",
            wealth_cost: 0,
            time_cost: 0
        }]);
    };

    const updateResource = (idx: number, field: string, value: any) => {
        const newResources = [...resources];
        newResources[idx] = { ...newResources[idx], [field]: value };
        setResources(newResources);
    };

    const removeResource = (idx: number) => {
        setResources(resources.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-amber-500 mb-2 flex items-center gap-2">
                    <Pickaxe className="w-4 h-4" /> 04. Material Abundance
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the subterranean wealth and industrial precursors of your civilizations.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Global Resource Pool</h3>
                    <div className="flex gap-2">
                        <button onClick={() => addResource('NATURAL')} className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full text-[9px] font-black uppercase text-amber-500 hover:bg-amber-500/20 transition-colors">
                            <Plus className="w-3 h-3" /> Natural
                        </button>
                        <button onClick={() => addResource('PRODUCED')} className="flex items-center gap-1.5 px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[9px] font-black uppercase text-zinc-300 hover:bg-white/10 transition-colors">
                            <Plus className="w-3 h-3" /> Produced
                        </button>
                    </div>
                </div>

                <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {resources.map((r, i) => (
                        <div key={i} className={`p-4 bg-zinc-900/40 border rounded-2xl transition-all duration-300 ${r.type === 'PRODUCED' ? 'border-white/5 bg-zinc-900/20' : 'border-amber-500/10 bg-amber-900/5'}`}>
                            <div className="flex items-center gap-3 mb-4">
                                <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${r.type === 'PRODUCED' ? 'bg-white/5 border-white/10' : 'bg-amber-500/10 border-amber-500/20'}`}>
                                    <span className="text-[10px] font-black text-amber-500">{r.type === 'NATURAL' ? 'N' : 'P'}</span>
                                </div>
                                <input
                                    type="text"
                                    value={r.name}
                                    onChange={e => updateResource(i, 'name', e.target.value)}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-amber-500 transition-colors"
                                    placeholder="RESOURCE_NAME"
                                />
                                <button onClick={() => removeResource(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-6 mb-4">
                                <div className="space-y-3">
                                    <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                        <span>Scarcity (R ↔ C)</span>
                                        <span className="text-white font-mono">{(r.scarcity * 100).toFixed(0)}%</span>
                                    </div>
                                    <input type="range" min="0" max="1" step="0.05" value={r.scarcity} onChange={e => updateResource(i, 'scarcity', Number(e.target.value))} className="w-full h-1 bg-zinc-800 accent-amber-500" />
                                </div>
                                <div className="flex items-center gap-3 pt-3">
                                    <label className="flex items-center gap-2 text-[10px] text-zinc-400 font-bold uppercase cursor-pointer group">
                                        <input type="checkbox" checked={r.is_infinite} onChange={e => updateResource(i, 'is_infinite', e.target.checked)} className="w-3 h-3 rounded bg-zinc-900 border-white/10 accent-amber-500" />
                                        <span className="group-hover:text-white transition-colors">Infinite Supply</span>
                                    </label>
                                </div>
                            </div>

                            {r.type === 'PRODUCED' ? (
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-3">
                                    <div className="flex items-center gap-2 text-[9px] font-black text-zinc-500 uppercase">
                                        <Info className="w-3 h-3" /> Production Logic
                                    </div>
                                    <div className="grid grid-cols-2 gap-3 mt-1">
                                        <div className="space-y-1">
                                            <span className="text-[8px] font-bold text-zinc-600 uppercase">Precursor</span>
                                            <input type="text" value={r.precursor_resource} onChange={e => updateResource(i, 'precursor_resource', e.target.value)} className="w-full bg-zinc-950 border border-white/5 p-1.5 rounded text-[10px] text-white outline-none" placeholder="None" />
                                        </div>
                                        <div className="space-y-1">
                                            <span className="text-[8px] font-bold text-zinc-600 uppercase">Wealth Cost</span>
                                            <input type="number" value={r.wealth_cost} onChange={e => updateResource(i, 'wealth_cost', Number(e.target.value))} className="w-full bg-zinc-950 border border-white/5 p-1.5 rounded text-[10px] text-white outline-none" />
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <span className="text-[9px] font-black text-zinc-500 uppercase">Natural Sources</span>
                                    <input
                                        type="text"
                                        value={Array.isArray(r.sources) ? r.sources.join(', ') : r.sources}
                                        onChange={e => updateResource(i, 'sources', e.target.value.split(',').map(s => s.trim()))}
                                        className="w-full bg-transparent border-b border-white/5 pb-1 text-[10px] text-zinc-300 focus:border-amber-500 outline-none placeholder:text-zinc-800"
                                        placeholder="Biomes, Flora, Fauna..."
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
