import React, { useEffect, useState } from 'react';

export const EntityEditor: React.FC = () => {
    const [entities, setEntities] = useState<{ factions: any[], resources: any[], wildlife: any[] }>({ factions: [], resources: [], wildlife: [] });
    const [activeTab, setActiveTab] = useState<'factions' | 'resources' | 'wildlife'>('factions');
    const [selectedEntity, setSelectedEntity] = useState<any>(null);
    const [configState, setConfigState] = useState<any>({});
    const [isSaving, setIsSaving] = useState(false);

    // Fetch the entities from our new Python API
    useEffect(() => {
        fetch('http://localhost:8001/api/lore/entities')
            .then(res => res.json())
            .then(data => setEntities(data))
            .catch(err => console.error("Failed to load entities:", err));
    }, []);

    return (
        <div className="w-full h-full bg-zinc-900 border-l border-zinc-700 text-zinc-300 flex flex-col font-mono text-xs">
            <div className="p-3 bg-black border-b border-zinc-700 font-bold text-yellow-500 uppercase tracking-widest">
                God Engine Config
            </div>

            {/* TABS */}
            <div className="flex border-b border-zinc-700">
                {['factions', 'resources', 'wildlife'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => { setActiveTab(tab as any); setSelectedEntity(null); }}
                        className={`flex-1 py-2 uppercase font-bold ${activeTab === tab ? 'bg-zinc-800 text-white' : 'hover:bg-zinc-800/50 text-zinc-500'}`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* LIST OF LORE ENTITIES */}
                <div className="w-1/3 border-r border-zinc-700 overflow-y-auto p-2 space-y-1">
                    {entities[activeTab].map((ent: any) => (
                        <button
                            key={ent.id}
                            onClick={() => { setSelectedEntity(ent); setConfigState({}); }}
                            className={`w-full text-left px-2 py-1 truncate ${selectedEntity?.id === ent.id ? 'bg-blue-900 text-white' : 'hover:bg-zinc-800'}`}
                        >
                            {ent.title.replace(/_/g, ' ')}
                        </button>
                    ))}
                    {entities[activeTab].length === 0 && <p className="text-zinc-600 p-2 italic">No {activeTab} found in Lore Vault.</p>}
                </div>

                {/* THE EDITOR PANEL */}
                <div className="w-2/3 p-4 overflow-y-auto space-y-4">
                    {selectedEntity ? (
                        <>
                            <h2 className="text-lg font-bold text-white uppercase border-b border-zinc-700 pb-1 mb-3">
                                {selectedEntity.title.replace(/_/g, ' ')}
                            </h2>

                            {/* FACTION VARIABLES */}
                            {activeTab === 'factions' && (
                                <>
                                    <label className="block">Archetype <span className="text-zinc-500 text-[10px]">(Sets Tech & Expansion)</span></label>
                                    <select value={configState.archetype || 'Nomad'} onChange={e => setConfigState({ ...configState, archetype: e.target.value })} className="w-full bg-black border border-zinc-700 p-1 text-white mb-2">
                                        <option>Nomad</option><option>Tribal</option><option>Monarchy</option>
                                    </select>
                                    <label className="block">Aggression Level ({(configState.aggression || 50)}%)</label>
                                    <input type="range" min="0" max="100" value={configState.aggression || 50} onChange={e => setConfigState({ ...configState, aggression: Number(e.target.value) })} className="w-full accent-yellow-500 mb-2" />
                                </>
                            )}

                            {/* RESOURCE VARIABLES */}
                            {activeTab === 'resources' && (
                                <>
                                    <label className="block">Utility Category</label>
                                    <select value={configState.utility || 'Food'} onChange={e => setConfigState({ ...configState, utility: e.target.value })} className="w-full bg-black border border-zinc-700 p-1 text-white mb-2">
                                        <option>Food</option><option>Construction Mat</option><option>Fuel</option><option>Magic/Aetherium</option><option>Wealth</option>
                                    </select>
                                    <label className="block">Rarity</label>
                                    <select value={configState.rarity || 'Common'} onChange={e => setConfigState({ ...configState, rarity: e.target.value })} className="w-full bg-black border border-zinc-700 p-1 text-white mb-2">
                                        <option>Common</option><option>Scarce</option><option>Rare</option><option>Mythic</option>
                                    </select>
                                    <label className="flex items-center space-x-2 mt-2">
                                        <input type="checkbox" checked={configState.is_finite || false} onChange={e => setConfigState({ ...configState, is_finite: e.target.checked })} className="accent-yellow-500" /> <span>Is Finite? (Can be depleted)</span>
                                    </label>
                                </>
                            )}

                            {/* WILDLIFE VARIABLES */}
                            {activeTab === 'wildlife' && (
                                <>
                                    <label className="block">Behavior Archetype</label>
                                    <select value={configState.behavior || 'Herding Prey'} onChange={e => setConfigState({ ...configState, behavior: e.target.value })} className="w-full bg-black border border-zinc-700 p-1 text-white mb-2">
                                        <option>Herding Prey</option><option>Pack Predator</option><option>Solo Predator</option><option>Passive Forager</option>
                                    </select>
                                    <label className="block">Diet</label>
                                    <select value={configState.diet || 'Herbivore'} onChange={e => setConfigState({ ...configState, diet: e.target.value })} className="w-full bg-black border border-zinc-700 p-1 text-white mb-2">
                                        <option>Herbivore</option><option>Carnivore</option><option>Omnivore</option>
                                    </select>
                                    <label className="flex items-center space-x-2 mt-2 border-t border-zinc-700 pt-2">
                                        <input type="checkbox" checked={configState.farmable || false} onChange={e => setConfigState({ ...configState, farmable: e.target.checked })} className="accent-yellow-500" /> <span>Farmable / Tamable</span>
                                    </label>
                                </>
                            )}

                            <button
                                onClick={async () => {
                                    setIsSaving(true);
                                    try {
                                        const payload = { id: selectedEntity.id, title: selectedEntity.title, type: activeTab, ...configState };
                                        const res = await fetch('http://localhost:8001/api/lore/config/save', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify(payload)
                                        });
                                        if (!res.ok) throw new Error("API Route Failed");
                                        alert("God Engine Params Saved!");
                                    } catch (e) {
                                        alert("Save Failed. Is Port 8001 running?");
                                    } finally {
                                        setIsSaving(false);
                                    }
                                }}
                                disabled={isSaving}
                                className="w-full mt-4 bg-zinc-800 hover:bg-zinc-700 text-white font-bold py-2 border border-zinc-600 tracking-wider disabled:opacity-50">
                                {isSaving ? "SAVING TO DB..." : "SAVE CONFIG TO ENGINE"}
                            </button>
                        </>
                    ) : (
                        <div className="flex h-full items-center justify-center text-zinc-600">
                            Select an entity to edit its God Engine rules.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
