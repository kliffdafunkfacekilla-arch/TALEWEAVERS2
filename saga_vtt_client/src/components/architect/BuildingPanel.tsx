import { Plus, Trash2, Landmark, Coins, TrendingUp } from 'lucide-react';

interface BuildingPanelProps {
    buildings: any[];
    setBuildings: (buildings: any[]) => void;
}

export const BuildingPanel: React.FC<BuildingPanelProps> = ({ buildings, setBuildings }) => {
    const addBuilding = () => {
        setBuildings([...buildings, {
            name: "New Structure",
            type: "Economic",
            minimum_tier: 1,
            build_cost: { Gold: 100 },
            upkeep: { Food: 1 },
            production: { Wealth: 10 }
        }]);
    };

    const updateBuilding = (idx: number, field: string, value: any) => {
        const newBuildings = [...buildings];
        newBuildings[idx] = { ...newBuildings[idx], [field]: value };
        setBuildings(newBuildings);
    };

    const removeBuilding = (idx: number) => {
        setBuildings(buildings.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-orange-600 mb-2 flex items-center gap-2">
                    <Landmark className="w-4 h-4" /> 09. Structural Blueprints
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the templates for architectural development and industrial specialization.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Architectural Templates</h3>
                    <button onClick={addBuilding} className="flex items-center gap-1.5 px-3 py-1 bg-orange-600/10 border border-orange-600/20 rounded-full text-[9px] font-black uppercase text-orange-600 hover:bg-orange-600/20 transition-colors">
                        <Plus className="w-3 h-3" /> New Template
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {buildings.map((b, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/40 border border-white/5 rounded-2xl hover:border-orange-600/30 transition-all duration-300">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-8 h-8 rounded-xl bg-zinc-800 flex items-center justify-center border border-white/5">
                                    <Landmark className="w-4 h-4 text-orange-500" />
                                </div>
                                <input
                                    type="text"
                                    value={b.name}
                                    onChange={e => updateBuilding(i, 'name', e.target.value)}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-orange-500 transition-colors"
                                    placeholder="BUILDING_NAME"
                                />
                                <button onClick={() => removeBuilding(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                    <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2">Category</span>
                                    <select
                                        value={b.type || "Economic"}
                                        onChange={e => updateBuilding(i, 'type', e.target.value)}
                                        className="w-full bg-transparent text-[10px] font-bold text-zinc-300 outline-none"
                                    >
                                        <option value="Economic">Economic</option>
                                        <option value="Military">Military</option>
                                        <option value="Civic">Civic</option>
                                        <option value="Religious">Religious</option>
                                    </select>
                                </div>
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                    <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2">Tech Level (1-5)</span>
                                    <input
                                        type="number" min="1" max="5"
                                        value={b.minimum_tier}
                                        onChange={e => updateBuilding(i, 'minimum_tier', Number(e.target.value))}
                                        className="w-full bg-transparent text-[10px] font-bold text-zinc-300 outline-none border-b border-white/5 focus:border-orange-500"
                                    />
                                </div>
                            </div>

                            {/* Yield & Upkeep */}
                            <div className="space-y-2">
                                <div className="p-3 bg-orange-600/5 border border-orange-600/10 rounded-xl flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <TrendingUp className="w-3 h-3 text-emerald-500" />
                                        <span className="text-[9px] font-black text-zinc-500 uppercase">Yield</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <input
                                            type="text" placeholder="Resource"
                                            value={Object.keys(b.production || {})[0] || ""}
                                            onChange={e => updateBuilding(i, 'production', { [e.target.value]: Object.values(b.production || {})[0] || 1 })}
                                            className="bg-transparent text-[10px] text-emerald-400 font-bold w-20 text-right outline-none"
                                        />
                                        <input
                                            type="number"
                                            value={Number(Object.values(b.production || {})[0] || 0)}
                                            onChange={e => updateBuilding(i, 'production', { [Object.keys(b.production || {})[0] || "Wealth"]: Number(e.target.value) })}
                                            className="bg-zinc-950 border border-white/5 rounded text-[10px] text-white w-10 text-center outline-none"
                                        />
                                    </div>
                                </div>
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Coins className="w-3 h-3 text-amber-500" />
                                        <span className="text-[9px] font-black text-zinc-500 uppercase">Upkeep</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <input
                                            type="text" placeholder="Resource"
                                            value={Object.keys(b.upkeep || {})[0] || ""}
                                            onChange={e => updateBuilding(i, 'upkeep', { [e.target.value]: Object.values(b.upkeep || {})[0] || 1 })}
                                            className="bg-transparent text-[10px] text-zinc-400 font-bold w-20 text-right outline-none"
                                        />
                                        <input
                                            type="number"
                                            value={Number(Object.values(b.upkeep || {})[0] || 0)}
                                            onChange={e => updateBuilding(i, 'upkeep', { [Object.keys(b.upkeep || {})[0] || "Food"]: Number(e.target.value) })}
                                            className="bg-zinc-950 border border-white/5 rounded text-[10px] text-white w-10 text-center outline-none"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
