import React from 'react';
import { Plus, Trash2, Sliders, Hash } from 'lucide-react';

interface BiomePanelProps {
    biomes: any[];
    setBiomes: (biomes: any[]) => void;
}

export const BiomePanel: React.FC<BiomePanelProps> = ({ biomes, setBiomes }) => {
    const addBiome = () => {
        setBiomes([...biomes, {
            name: "NEW_BIOME",
            min_temp: 0, max_temp: 20,
            min_rain: 10, max_rain: 50,
            color: "#4ade80"
        }]);
    };

    const updateBiome = (idx: number, field: string, value: any) => {
        const newBiomes = [...biomes];
        newBiomes[idx] = { ...newBiomes[idx], [field]: value };
        setBiomes(newBiomes);
    };

    const removeBiome = (idx: number) => {
        setBiomes(biomes.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-orange-400 mb-2 flex items-center gap-2">
                    <Hash className="w-4 h-4" /> 03. Ecological Zoning
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the thresholds for biological emergence across your global canvas.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Biome Classifications</h3>
                    <button
                        onClick={addBiome}
                        className="flex items-center gap-1.5 px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[9px] font-black uppercase text-zinc-300 hover:bg-white/10 transition-colors"
                    >
                        <Plus className="w-3 h-3" /> New Class
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {biomes.map((b, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/40 border border-white/5 rounded-2xl hover:border-orange-500/30 transition-all duration-300">
                            <div className="flex items-center gap-2 mb-4">
                                <input
                                    type="text"
                                    value={b.name}
                                    onChange={e => updateBiome(i, 'name', e.target.value.toUpperCase().replace(/\s+/g, '_'))}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-orange-400 transition-colors"
                                    placeholder="BIOME_TAG"
                                />
                                <button onClick={() => removeBiome(i)} className="text-zinc-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                {/* Temp Range */}
                                <div className="space-y-3">
                                    <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase">
                                        <span>Temp Range</span>
                                        <span className="text-white font-mono">{b.min_temp}°/{b.max_temp}°</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <input type="range" min="-100" max="100" value={b.min_temp} onChange={e => updateBiome(i, 'min_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-orange-500" />
                                        <input type="range" min="-100" max="100" value={b.max_temp} onChange={e => updateBiome(i, 'max_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-orange-500" />
                                    </div>
                                </div>

                                {/* Moisture Range */}
                                <div className="space-y-3">
                                    <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase">
                                        <span>Moisture %</span>
                                        <span className="text-white font-mono">{b.min_rain}/{b.max_rain}</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <input type="range" min="0" max="100" value={b.min_rain} onChange={e => updateBiome(i, 'min_rain', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-blue-400" />
                                        <input type="range" min="0" max="100" value={b.max_rain} onChange={e => updateBiome(i, 'max_rain', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-blue-400" />
                                    </div>
                                </div>
                            </div>

                            {/* Advanced Toggle/Color (Optional Visual Polish) */}
                            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: b.color || '#4ade80' }} />
                                    <span className="text-[9px] font-bold text-zinc-600 uppercase">Visual Layer Mapping</span>
                                </div>
                                <button className="text-zinc-600 hover:text-white transition-colors">
                                    <Sliders className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
