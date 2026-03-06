import { Plus, Trash2, Trees, Thermometer, Droplets, Utensils } from 'lucide-react';

interface LifeformPanelProps {
    lifeforms: any[];
    setLifeforms: (lifeforms: any[]) => void;
}

export const LifeformPanel: React.FC<LifeformPanelProps> = ({ lifeforms, setLifeforms }) => {
    const addEntity = (type: 'FAUNA' | 'FLORA') => {
        setLifeforms([...lifeforms, {
            name: `New ${type === 'FAUNA' ? 'Fauna' : 'Flora'}`,
            type: type,
            is_aggressive: false,
            is_farmable: type === 'FLORA',
            is_tameable: false,
            farm_yield_resource: "Fiber",
            farm_yield_amount: 10,
            harvest_resource: "Bones",
            harvest_amount: 2,
            is_harvest_fatal: true,
            min_temp: 10, max_temp: 40,
            min_water: 0.1, max_water: 1.0,
            spawn_chance: 0.1,
            diet: type === 'FLORA' ? ["Sunlight"] : ["Plants"]
        }]);
    };

    const updateEntity = (idx: number, field: string, value: any) => {
        const newLifeforms = [...lifeforms];
        newLifeforms[idx] = { ...newLifeforms[idx], [field]: value };
        setLifeforms(newLifeforms);
    };

    const removeEntity = (idx: number) => {
        setLifeforms(lifeforms.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-emerald-500 mb-2 flex items-center gap-2">
                    <Trees className="w-4 h-4" /> 05. Biomass & Biosphere
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Seed your world with living entities and define the trophic levels of the ecosystem.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Biological Entities</h3>
                    <div className="flex gap-2">
                        <button onClick={() => addEntity('FAUNA')} className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[9px] font-black uppercase text-emerald-500 hover:bg-emerald-500/20 transition-colors">
                            <Plus className="w-3 h-3" /> Fauna
                        </button>
                        <button onClick={() => addEntity('FLORA')} className="flex items-center gap-1.5 px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[9px] font-black uppercase text-zinc-300 hover:bg-white/10 transition-colors">
                            <Plus className="w-3 h-3" /> Flora
                        </button>
                    </div>
                </div>

                <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {lifeforms.map((lf, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/40 border border-white/5 rounded-2xl hover:border-emerald-500/30 transition-all duration-300">
                            <div className="flex items-center gap-3 mb-4">
                                <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${lf.type === 'FAUNA' ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-emerald-900/10 border-emerald-900/20'}`}>
                                    <span className="text-[10px] font-black text-emerald-500">{lf.type === 'FAUNA' ? 'A' : 'V'}</span>
                                </div>
                                <input
                                    type="text"
                                    value={lf.name}
                                    onChange={e => updateEntity(i, 'name', e.target.value)}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-emerald-500 transition-colors"
                                    placeholder="ENTITY_NAME"
                                />
                                <button onClick={() => removeEntity(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-6 mb-6">
                                {/* Environmental Ranges */}
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span className="flex items-center gap-1"><Thermometer className="w-3 h-3" /> Temp Threshold</span>
                                            <span className="text-white font-mono">{lf.min_temp}°/{lf.max_temp}°</span>
                                        </div>
                                        <div className="flex gap-2">
                                            <input type="range" min="-100" max="100" value={lf.min_temp} onChange={e => updateEntity(i, 'min_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-emerald-500" />
                                            <input type="range" min="-100" max="100" value={lf.max_temp} onChange={e => updateEntity(i, 'max_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-emerald-500" />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span className="flex items-center gap-1"><Droplets className="w-3 h-3" /> Water Needs</span>
                                            <span className="text-white font-mono">{lf.min_water.toFixed(1)}/{lf.max_water.toFixed(1)}</span>
                                        </div>
                                        <div className="flex gap-2">
                                            <input type="range" min="0" max="2" step="0.1" value={lf.min_water} onChange={e => updateEntity(i, 'min_water', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-cyan-500" />
                                            <input type="range" min="0" max="2" step="0.1" value={lf.max_water} onChange={e => updateEntity(i, 'max_water', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-800 accent-cyan-500" />
                                        </div>
                                    </div>
                                </div>

                                {/* Diet & Spawn */}
                                <div className="space-y-4 text-xs">
                                    <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                        <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2"><Utensils className="w-3 h-3" /> {lf.type === 'FLORA' ? 'NEEDS' : 'DIET'}</span>
                                        <input
                                            type="text"
                                            value={lf.diet?.join(', ')}
                                            onChange={e => updateEntity(i, 'diet', e.target.value.split(',').map(s => s.trim()))}
                                            className="w-full bg-transparent text-[10px] text-zinc-300 outline-none border-b border-white/5 focus:border-emerald-500"
                                            placeholder="Water, Sunlight, Meat..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <div className="flex justify-between text-[8px] font-bold text-zinc-600 uppercase tracking-widest">
                                            <span>Abundance</span>
                                            <span className="text-zinc-400">{(lf.spawn_chance * 100).toFixed(0)}%</span>
                                        </div>
                                        <input type="range" min="0" max="1" step="0.01" value={lf.spawn_chance} onChange={e => updateEntity(i, 'spawn_chance', Number(e.target.value))} className="w-full h-1 bg-zinc-800 accent-zinc-500" />
                                    </div>
                                </div>
                            </div>

                            {/* Options & Output */}
                            <div className="grid grid-cols-3 gap-2">
                                <label className="p-2 border border-white/5 rounded-xl flex flex-col items-center gap-1 cursor-pointer hover:bg-white/5 transition-colors">
                                    <input type="checkbox" checked={lf.is_aggressive} onChange={e => updateEntity(i, 'is_aggressive', e.target.checked)} className="accent-emerald-500" />
                                    <span className="text-[8px] font-black text-zinc-500 uppercase">Aggressive</span>
                                </label>
                                <label className="p-2 border border-white/5 rounded-xl flex flex-col items-center gap-1 cursor-pointer hover:bg-white/5 transition-colors">
                                    <input type="checkbox" checked={lf.is_farmable} onChange={e => updateEntity(i, 'is_farmable', e.target.checked)} className="accent-emerald-500" />
                                    <span className="text-[8px] font-black text-zinc-500 uppercase">Farmable</span>
                                </label>
                                <label className="p-2 border border-white/5 rounded-xl flex flex-col items-center gap-1 cursor-pointer hover:bg-white/5 transition-colors">
                                    <input type="checkbox" checked={lf.is_tameable} onChange={e => updateEntity(i, 'is_tameable', e.target.checked)} className="accent-emerald-500" />
                                    <span className="text-[8px] font-black text-zinc-500 uppercase">Tameable</span>
                                </label>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
