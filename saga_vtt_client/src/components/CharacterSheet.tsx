import React, { useState, useEffect } from 'react';
import speciesData from '../data/Species_Slots.json';

export const CharacterSheet: React.FC = () => {
    const [name, setName] = useState('Subject 001');
    const [species, setSpecies] = useState('PLANT');

    // Core Attributes (The 6/6 Split)
    const [stats, setStats] = useState({
        might: 10, endurance: 10, vitality: 10, fortitude: 10, reflexes: 10, finesse: 10,
        knowledge: 10, logic: 10, charm: 10, willpower: 10, awareness: 10, intuition: 10
    });

    // Tactical Skills Tracking (skillName -> "Body" | "Mind")
    const [tacticalSkills, setTacticalSkills] = useState<{ [key: string]: string }>({});

    // Toggle a Tactical Skill Lead
    const toggleSkillLead = (skill: string) => {
        setTacticalSkills(prev => {
            const next = { ...prev };
            if (!next[skill]) next[skill] = "Body";
            else if (next[skill] === "Body") next[skill] = "Mind";
            else delete next[skill]; // Cycle to off
            return next;
        });
    };

    // The 8-Slot Biology System (Includes Size and Ancestry)
    const [evolutions, setEvolutions] = useState({
        size_slot: 'Standard', ancestry_slot: 'Standard',
        head_slot: 'Standard', body_slot: 'Standard', arms_slot: 'Standard',
        legs_slot: 'Standard', skin_slot: 'Standard', special_slot: 'Standard'
    });

    // Reset slots to "Standard" when species changes, to avoid invalid options
    useEffect(() => {
        setEvolutions({
            size_slot: 'Standard', ancestry_slot: 'Standard',
            head_slot: 'Standard', body_slot: 'Standard', arms_slot: 'Standard',
            legs_slot: 'Standard', skin_slot: 'Standard', special_slot: 'Standard'
        });
    }, [species]);

    const [compiledData, setCompiledData] = useState<any>(null);
    const [isCalculating, setIsCalculating] = useState(false);

    // Derive currently available bodily options from the JSON DB based on Species Base
    const currentSpeciesOptions = (speciesData as any)[species] || {};

    // Extracting just names from triads list for simple UI mockup since we can't fetch easily here directly without breaking Vite setup
    const tacticalTriads = {
        "Assault": ["Aggressive", "Calculated", "Patient"],
        "Coercion": ["Intimidating", "Deception", "Relentless"],
        "Ballistics": ["Skirmish", "Precise", "Thrown/Tossed"],
        "Suppression": ["Predict", "Impose", "Imply"],
        "Fortify": ["Rooted", "Fluid", "Dueling"],
        "Resolve": ["Confidence", "Reasoning", "Cavalier"],
        "Operations": ["Alter", "Utilize", "Introduce"],
        "Tactics": ["Command", "Exploit", "Tactics"],
        "Stabilize": ["First Aid", "Medicine", "Surgery"],
        "Rally": ["Self-Awareness", "Detached", "Mindfulness"],
        "Mobility": ["Charge", "Flanking", "Speed"],
        "Bravery": ["Commitment", "Determined", "Outsmart"]
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
                    tactical_skills: tacticalSkills,
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

                {/* THE 12 BASE ATTRIBUTES */}
                <div className="bg-black p-4 border border-zinc-800">
                    <h2 className="text-yellow-500 font-bold uppercase mb-4 flex justify-between">
                        <span>Genetic Attributes</span>
                        <span className="text-zinc-500 text-xs">Total: {Object.values(stats).reduce((a, b) => a + b, 0)}</span>
                    </h2>
                    <div className="grid grid-cols-2 gap-6">
                        {/* SECTOR I: PHYSICAL */}
                        <div className="space-y-2 border-r border-zinc-800 pr-4">
                            <div className="text-red-500 font-bold text-xs uppercase mb-2 border-b border-red-900 pb-1">Sector I: Body</div>
                            {['might', 'endurance', 'vitality', 'fortitude', 'reflexes', 'finesse'].map(stat => (
                                <div key={stat} className="flex justify-between items-center bg-zinc-900 border border-zinc-800 px-2 py-1">
                                    <span className="text-[10px] text-zinc-400 uppercase w-20">{stat}</span>
                                    <div className="flex gap-2 items-center">
                                        <button onClick={() => setStats(prev => ({ ...prev, [stat]: Math.max(0, prev[stat as keyof typeof stats] - 1) }))} className="text-red-500 hover:text-white">-</button>
                                        <span className="text-white font-bold w-6 text-center">{stats[stat as keyof typeof stats]}</span>
                                        <button onClick={() => setStats(prev => ({ ...prev, [stat]: prev[stat as keyof typeof stats] + 1 }))} className="text-green-500 hover:text-white">+</button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* SECTOR II: MENTAL */}
                        <div className="space-y-2">
                            <div className="text-blue-500 font-bold text-xs uppercase mb-2 border-b border-blue-900 pb-1">Sector II: Mind</div>
                            {['knowledge', 'logic', 'charm', 'willpower', 'awareness', 'intuition'].map(stat => (
                                <div key={stat} className="flex justify-between items-center bg-zinc-900 border border-zinc-800 px-2 py-1">
                                    <span className="text-[10px] text-zinc-400 uppercase w-20">{stat}</span>
                                    <div className="flex gap-2 items-center">
                                        <button onClick={() => setStats(prev => ({ ...prev, [stat]: Math.max(0, prev[stat as keyof typeof stats] - 1) }))} className="text-red-500 hover:text-white">-</button>
                                        <span className="text-white font-bold w-6 text-center">{stats[stat as keyof typeof stats]}</span>
                                        <button onClick={() => setStats(prev => ({ ...prev, [stat]: prev[stat as keyof typeof stats] + 1 }))} className="text-green-500 hover:text-white">+</button>
                                    </div>
                                </div>
                            ))}
                        </div>
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
                                    {currentSpeciesOptions[slot]?.map((opt: string) => (
                                        <option key={opt} value={opt}>{opt}</option>
                                    ))}
                                </select>
                            </div>
                        ))}
                    </div>
                </div>

                {/* THE 36 TACTICAL SKILLS */}
                <div className="bg-black p-4 border border-zinc-800">
                    <h2 className="text-yellow-500 font-bold uppercase mb-4">Tactical Skills (The 36)</h2>
                    <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                        {Object.entries(tacticalTriads).map(([group, skills]) => (
                            <div key={group} className="bg-zinc-900 border border-zinc-800 p-2">
                                <span className="text-yellow-600 font-bold text-[10px] uppercase block mb-1">{group}</span>
                                {skills.map(skill => (
                                    <div key={skill} className="flex justify-between items-center text-xs text-zinc-300 py-1 border-t border-zinc-800/50">
                                        <span className="truncate w-2/3">{skill}</span>
                                        <button
                                            onClick={() => toggleSkillLead(skill)}
                                            className={`text-[10px] px-1 rounded font-bold w-10 text-center ${!tacticalSkills[skill] ? 'text-zinc-600 hover:text-white' : tacticalSkills[skill] === 'Body' ? 'bg-red-900 text-red-100' : 'bg-blue-900 text-blue-100'}`}
                                        >
                                            {tacticalSkills[skill] ? tacticalSkills[skill].toUpperCase() : 'OFF'}
                                        </button>
                                    </div>
                                ))}
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

                        {/* TACTICAL SKILLS (Calculated Ranks & Pips) */}
                        {compiledData.tactical_skills && Object.keys(compiledData.tactical_skills).length > 0 && (
                            <div>
                                <h3 className="text-yellow-500 font-bold uppercase border-b border-zinc-800 pb-1 mb-2">Tactical Aptitude</h3>
                                <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(compiledData.tactical_skills).map(([skill, data]: [string, any]) => (
                                        <div key={skill} className="bg-zinc-900 p-2 border border-zinc-800 flex justify-between items-center">
                                            <div className="text-white font-bold text-xs">{skill}</div>
                                            <div className="flex gap-2 text-[10px]">
                                                <span className="text-zinc-400">Rank <span className="text-yellow-500 font-bold text-sm">{data.rank}</span></span>
                                                <span className="text-zinc-600">Pips <span className="text-zinc-300">{data.pips}/4</span></span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

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
