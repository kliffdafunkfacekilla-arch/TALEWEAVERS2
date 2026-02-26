import React, { useState } from 'react';

export const CharacterSheet: React.FC = () => {
    const [name, setName] = useState('Subject 001');
    const [species, setSpecies] = useState('PLANT');

    // Core Attributes (The 6/6 Split)
    const [stats] = useState({
        might: 10, endurance: 10, vitality: 10, fortitude: 10, reflexes: 10, finesse: 10,
        knowledge: 10, logic: 10, charm: 10, willpower: 10, awareness: 10, intuition: 10
    });

    // The 6-Slot Biology System
    const [evolutions, setEvolutions] = useState({
        head_slot: 'Standard', body_slot: 'Standard', arms_slot: 'Standard',
        legs_slot: 'Standard', skin_slot: 'Standard', special_slot: 'Standard'
    });

    const [compiledData, setCompiledData] = useState<any>(null);
    const [isCalculating, setIsCalculating] = useState(false);

    // Hardcoded dropdown options for demonstration (In production, you'd fetch these from the API)
    const options = {
        head_slot: ['Standard', 'Flower Head', 'Gnarled Face', 'Mushroom Cap', 'Hooked Beak', 'Sharp Eyes'],
        body_slot: ['Standard', 'IronBark', 'Cactus Core', 'Barrel Chest', 'Mossy Skin'],
        arms_slot: ['Standard', 'Tendril Fingers', 'Razor Leaves', 'Large Talons', 'Retractable Claws'],
        legs_slot: ['Standard', 'Wide Roots', 'Webbed Feet', 'Hooves', 'Jumping Legs'],
        skin_slot: ['Standard', 'Adaptive Leaves', 'Cactus Spines', 'Black Plumage', 'Metallic Scales'],
        special_slot: ['Standard', 'Toxic Sap', 'Pine Cones', 'Syrinx Box', 'Prehensile Tail']
    };

    const calculateCharacter = async () => {
        setIsCalculating(true);
        try {
            const response = await fetch('http://localhost:8003/api/rules/character/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    base_attributes: stats,
                    evolutions: { species_base: species, ...evolutions },
                    background_training: 'Survivor',
                    selected_powers: [],
                    equipped_loadout: { armor: "None", weapon: "None" }
                })
            });
            const data = await response.json();
            setCompiledData(data);
        } catch (error) {
            console.error("Failed to compile character:", error);
        }
        setIsCalculating(false);
    };

    return (
        <div className="flex w-full h-full bg-black text-zinc-300 font-mono text-sm overflow-hidden">

            {/* LEFT PANEL: THE BUILDER */}
            <div className="w-1/2 overflow-y-auto p-6 border-r border-zinc-700 space-y-6 bg-zinc-900">
                <h1 className="text-2xl font-bold text-yellow-500 uppercase tracking-widest border-b border-zinc-700 pb-2">
                    T.A.L.E.W.E.A.V.E.R. Origin Forge
                </h1>

                {/* BASIC INFO */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs text-zinc-500 uppercase">Designation</label>
                        <input type="text" value={name} onChange={e => setName(e.target.value)} className="w-full bg-black border border-zinc-700 p-2 text-white" />
                    </div>
                    <div>
                        <label className="text-xs text-zinc-500 uppercase">Species Base</label>
                        <select value={species} onChange={e => setSpecies(e.target.value)} className="w-full bg-black border border-zinc-700 p-2 text-white">
                            <option value="PLANT">Plant</option>
                            <option value="AVIAN">Avian</option>
                            <option value="REPTILE">Reptile</option>
                            <option value="INSECT">Insect</option>
                            <option value="MAMMAL">Mammal</option>
                            <option value="AQUATIC">Aquatic</option>
                        </select>
                    </div>
                </div>

                {/* BIOLOGICAL EVOLUTIONS (6-SLOT) */}
                <div className="bg-black p-4 border border-zinc-800">
                    <h2 className="text-yellow-500 font-bold uppercase mb-4">Biological Mutations</h2>
                    <div className="grid grid-cols-2 gap-4">
                        {Object.keys(evolutions).map((slot) => (
                            <div key={slot}>
                                <label className="text-[10px] text-zinc-500 uppercase">{slot.replace('_', ' ')}</label>
                                <select
                                    value={(evolutions as any)[slot]}
                                    onChange={e => setEvolutions({ ...evolutions, [slot]: e.target.value })}
                                    className="w-full bg-zinc-900 border border-zinc-700 p-1 text-white text-xs"
                                >
                                    {(options as any)[slot].map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
                                </select>
                            </div>
                        ))}
                    </div>
                </div>

                <button
                    onClick={calculateCharacter} disabled={isCalculating}
                    className="w-full bg-yellow-600 hover:bg-yellow-500 text-black font-bold py-3 uppercase tracking-widest transition-colors"
                >
                    {isCalculating ? "Sequencing DNA..." : "Compile Vitals"}
                </button>
            </div>

            {/* RIGHT PANEL: THE RESULTING CHARACTER SHEET */}
            <div className="w-1/2 overflow-y-auto p-6 bg-black">
                {compiledData ? (
                    <div className="space-y-6 animate-fade-in">
                        <div className="border-b border-zinc-700 pb-2">
                            <h2 className="text-3xl font-bold text-white uppercase">{compiledData.name}</h2>
                            <p className="text-zinc-500">Bio-Signature: {compiledData.evolutions?.species_base}</p>
                        </div>

                        {/* SURVIVAL POOLS (Derived from Math!) */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-red-900/20 border border-red-900 p-4 rounded">
                                <div className="text-red-500 font-bold text-xs uppercase">HP / Meat</div>
                                <div className="text-3xl text-white font-bold">{compiledData.vitals?.max_hp || 0}</div>
                            </div>
                            <div className="bg-orange-900/20 border border-orange-900 p-4 rounded">
                                <div className="text-orange-500 font-bold text-xs uppercase">Stamina</div>
                                <div className="text-3xl text-white font-bold">{compiledData.vitals?.max_stamina || 0}</div>
                            </div>
                            <div className="bg-blue-900/20 border border-blue-900 p-4 rounded">
                                <div className="text-blue-500 font-bold text-xs uppercase">Composure</div>
                                <div className="text-3xl text-white font-bold">{compiledData.vitals?.max_composure || 0}</div>
                            </div>
                            <div className="bg-purple-900/20 border border-purple-900 p-4 rounded">
                                <div className="text-purple-500 font-bold text-xs uppercase">Focus</div>
                                <div className="text-3xl text-white font-bold">{compiledData.vitals?.max_focus || 0}</div>
                            </div>
                        </div>

                        {/* GRANTED PASSIVES */}
                        <div>
                            <h3 className="text-yellow-500 font-bold uppercase border-b border-zinc-800 pb-1 mb-2">Granted Genetics</h3>
                            <div className="space-y-2">
                                {compiledData.passives && compiledData.passives.length > 0 ? compiledData.passives.map((passive: any, idx: number) => (
                                    <div key={idx} className="bg-zinc-900 p-2 border border-zinc-800">
                                        <div className="text-white font-bold text-xs">{passive.name} <span className="text-zinc-500 text-[10px]">[{passive.type}]</span></div>
                                        <div className="text-zinc-400 text-xs mt-1">{passive.effect}</div>
                                    </div>
                                )) : <div className="text-zinc-600 italic">No mutations detected.</div>}
                            </div>
                        </div>

                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-zinc-700 italic">
                        Awaiting genetic sequence compilation...
                    </div>
                )}
            </div>
        </div>
    );
};
