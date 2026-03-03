import React, { useState, useEffect, useMemo } from 'react';
import { useGameStore } from '../store/useGameStore';
import { useCharacterStore } from '../store/useCharacterStore';
import speciesSlots from '../data/Species_Slots.json';
import speciesBases from '../data/species_base_stats.json';
import evolutionMatrix from '../data/Evolution_Matrix.json';
import tacticalTriads from '../data/tactical_triads.json';
import schoolsData from '../data/schools_of_power.json';

export const CharacterSheet: React.FC = () => {
    const [name, setName] = useState('Subject 001');
    const [species, setSpecies] = useState('PLANT');

    // 12 Tactical Skills (1 per triad)
    // Map: TriadName -> { skill: string, lead: "Body" | "Mind" }
    const [selectedSkills, setSelectedSkills] = useState<{ [key: string]: { skill: string, lead: string } }>({});

    // 8 Biological Mutations
    const [evolutions, setEvolutions] = useState({
        size_slot: 'Standard', ancestry_slot: 'Standard',
        head_slot: 'Standard', body_slot: 'Standard', arms_slot: 'Standard',
        legs_slot: 'Standard', skin_slot: 'Standard', special_slot: 'Standard'
    });

    // 2 Tier 1 Spells
    const [selectedSpells, setSelectedSpells] = useState<string[]>([]);

    const [compiledData, setCompiledData] = useState<any>(null);
    const [isCalculating, setIsCalculating] = useState(false);

    // Dynamic Calculation of current Stats (Mirroring Backend)
    const currentStats = useMemo(() => {
        const baseKey = species.charAt(0).toUpperCase() + species.slice(1).toLowerCase();
        const base = (speciesBases as any)[baseKey] || {};

        const stats = {
            might: base.might || 10, endurance: base.endurance || 10,
            vitality: base.vitality || 10, fortitude: base.fortitude || 10,
            reflexes: base.reflexes || 10, finesse: base.finesse || 10,
            knowledge: base.knowledge || 10, logic: base.logic || 10,
            charm: base.charm || 10, willpower: base.willpower || 10,
            awareness: base.awareness || 10, intuition: base.intuition || 10
        };

        const BODY_STATS = ["might", "endurance", "vitality", "fortitude", "reflexes", "finesse"];
        const MIND_STATS = ["knowledge", "logic", "charm", "willpower", "awareness", "intuition"];

        // Apply mutation bonuses (+1 to stats per choice)
        const chosenMutations = Object.values(evolutions);
        evolutionMatrix.forEach((trait: any) => {
            if (chosenMutations.includes(trait.name) && trait.name !== "Standard") {
                Object.entries(trait.stats || {}).forEach(([key, val]: [string, any]) => {
                    const potentialStats = key.replace('+', '').split(',').map(s => s.trim().toLowerCase());
                    potentialStats.forEach(ps => {
                        const cleanKey = ps.includes('reflex') ? 'reflexes' : ps.match(/[a-z]+/)?.[0];
                        if (cleanKey && stats.hasOwnProperty(cleanKey)) {
                            const bonus = typeof val === 'number' ? val : 1;
                            (stats as any)[cleanKey] += bonus;
                        }
                    });
                });
            }
        });

        // Apply Skill Bonuses (+1 to LEAD stat only)
        Object.values(selectedSkills).forEach((choice: any) => {
            const skillData = (Object.values(tacticalTriads).flat() as any[]).find(s => s.skill === choice.skill);
            if (skillData) {
                const parts = skillData.stat_pair.split('+').map((s: string) => s.trim().toLowerCase().replace('reflex', 'reflexes'));

                const bodyStat = parts.find((p: any) => BODY_STATS.includes(p)) || parts[0];
                const mindStat = parts.find((p: any) => MIND_STATS.includes(p)) || parts[1];

                const leadStat = choice.lead === "Body" ? bodyStat : mindStat;
                if ((stats as any).hasOwnProperty(leadStat)) (stats as any)[leadStat] += 1;
            }
        });

        return stats;
    }, [species, evolutions, selectedSkills]);

    // Cleanup when species changes
    useEffect(() => {
        setEvolutions({
            size_slot: 'Standard', ancestry_slot: 'Standard',
            head_slot: 'Standard', body_slot: 'Standard', arms_slot: 'Standard',
            legs_slot: 'Standard', skin_slot: 'Standard', special_slot: 'Standard'
        });
        setSelectedSpells([]);
        setSelectedSkills({});
    }, [species]);

    const toggleSkill = (triad: string, skill: string) => {
        setSelectedSkills(prev => {
            const current = prev[triad];
            if (current?.skill === skill) {
                if (current.lead === "Body") {
                    return { ...prev, [triad]: { ...current, lead: "Mind" } };
                } else {
                    const next = { ...prev };
                    delete next[triad];
                    return next;
                }
            } else {
                return { ...prev, [triad]: { skill, lead: "Body" } };
            }
        });
    };

    const toggleSpell = (spell: string) => {
        setSelectedSpells(prev => {
            if (prev.includes(spell)) return prev.filter(s => s !== spell);
            if (prev.length >= 2) return prev;
            return [...prev, spell];
        });
    };

    const calculateCharacter = async () => {
        if (Object.keys(selectedSkills).length !== 12) {
            alert("Please select 1 skill from EACH of the 12 triads.");
            return;
        }
        const bodyLeads = Object.values(selectedSkills).filter(s => s.lead === "Body").length;
        if (bodyLeads !== 6) {
            alert(`You must have a 6/6 Body/Mind split. Current: ${bodyLeads} Body, ${12 - bodyLeads} Mind.`);
            return;
        }

        setIsCalculating(true);
        try {
            const payloadSkillMap: { [key: string]: string } = {};
            Object.values(selectedSkills).forEach(s => payloadSkillMap[s.skill] = s.lead);

            const response = await fetch('http://localhost:8003/api/rules/character/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    base_attributes: null,
                    evolutions: { species_base: species, ...evolutions },
                    tactical_skills: payloadSkillMap,
                    selected_powers: selectedSpells.map(s => ({ name: s })),
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

    const bodyLeads = Object.values(selectedSkills).filter(s => s.lead === "Body").length;
    const mindLeads = Object.values(selectedSkills).length - bodyLeads;

    return (
        <div className="flex w-full h-full bg-black text-zinc-300 font-mono text-sm overflow-hidden">

            {/* LEFT PANEL: THE BUILDER */}
            <div className="w-1/2 overflow-y-auto p-6 border-r border-zinc-700 space-y-6 bg-zinc-900 custom-scrollbar">
                <div className="pb-4 border-b border-zinc-700">
                    <h1 className="text-2xl font-bold text-yellow-500 uppercase tracking-widest leading-tight">
                        T.A.L.E.W.E.A.V.E.R. <br /><span className="text-white">Soulweave Origin</span>
                    </h1>
                    <p className="text-[10px] text-zinc-500 mt-1 italic">Aetheric Configuration Active</p>
                </div>

                {/* BASIC INFO */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-[10px] text-zinc-500 uppercase">True Name / Identity</label>
                        <input type="text" value={name} onChange={e => setName(e.target.value)} className="w-full bg-black border border-zinc-700 p-2 text-white outline-none focus:border-yellow-500 transition-colors" />
                    </div>
                    <div>
                        <label className="text-[10px] text-zinc-500 uppercase">Species Base</label>
                        <select value={species} onChange={e => setSpecies(e.target.value)} className="w-full bg-black border border-zinc-700 p-2 text-white outline-none focus:border-yellow-500">
                            <option value="PLANT">Plant</option>
                            <option value="AVIAN">Avian</option>
                            <option value="REPTILE">Reptile</option>
                            <option value="INSECT">Insect</option>
                            <option value="MAMMAL">Mammal</option>
                            <option value="AQUATIC">Aquatic</option>
                        </select>
                    </div>
                </div>

                {/* DYNAMIC ATTRIBUTE PREVIEW */}
                <div className="bg-black p-4 border border-zinc-800 shadow-xl">
                    <h2 className="text-yellow-500 font-bold uppercase mb-4 text-xs tracking-widest border-l-2 border-yellow-600 pl-2">
                        Innate Soul Attributes
                    </h2>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-1">
                        {Object.entries(currentStats).map(([stat, val]) => (
                            <div key={stat} className="flex justify-between items-center border-b border-zinc-900 py-1">
                                <span className="text-[10px] text-zinc-500 uppercase">{stat}</span>
                                <span className={`font-bold ${val >= 12 ? 'text-purple-400' : 'text-zinc-200'}`}>{val}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* BIOLOGICAL EVOLUTIONS */}
                <div className="bg-black p-4 border border-zinc-800">
                    <h2 className="text-yellow-500 font-bold uppercase mb-4 text-xs tracking-widest border-l-2 border-yellow-600 pl-2">
                        8-Slot Mutations
                    </h2>
                    <div className="grid grid-cols-2 gap-4">
                        {Object.keys(evolutions).map((slot) => {
                            const selectedName = (evolutions as any)[slot];
                            const traitData = evolutionMatrix.find((t: any) => t.name === selectedName);
                            const effect = (traitData?.passives?.[0] as any)?.effect || (traitData as any)?.effect || "No description available.";
                            return (
                                <div key={slot} className="group relative">
                                    <label className="text-[10px] text-zinc-500 uppercase block mb-1">{slot.replace('_', ' ')}</label>
                                    <select
                                        value={selectedName}
                                        onChange={e => setEvolutions({ ...evolutions, [slot]: e.target.value })}
                                        className="w-full bg-zinc-900 border border-zinc-700 p-1 text-white text-xs outline-none focus:border-yellow-500"
                                    >
                                        {(speciesSlots as any)[species]?.[slot]?.map((opt: string) => (
                                            <option key={opt} value={opt}>{opt}</option>
                                        ))}
                                    </select>
                                    <div className="hidden group-hover:block absolute z-10 top-full left-0 mt-1 p-2 bg-zinc-800 border border-zinc-600 text-[10px] w-64 shadow-2xl rounded">
                                        <p className="text-yellow-500 font-bold mb-1">{selectedName}</p>
                                        {effect}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* TACTICAL SKILLS */}
                <div className="bg-black p-4 border border-zinc-800">
                    <h2 className="text-yellow-500 font-bold uppercase mb-4 text-xs tracking-widest border-l-2 border-yellow-600 pl-2 flex justify-between">
                        <span>The 12 Learned Skills</span>
                        <div className="flex gap-3 text-[9px] uppercase">
                            <span className={bodyLeads === 6 ? 'text-green-500' : 'text-red-500'}>Body: {bodyLeads}/6</span>
                            <span className={mindLeads === 6 ? 'text-green-500' : 'text-red-500'}>Mind: {mindLeads}/6</span>
                        </div>
                    </h2>
                    <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
                        {Object.entries(tacticalTriads).map(([group, skills]) => {
                            const selection = selectedSkills[group];
                            return (
                                <div key={group} className={`p-2 border ${selection ? 'border-zinc-700 bg-zinc-900' : 'border-zinc-800 bg-zinc-950'}`}>
                                    <span className="text-yellow-600 font-bold text-[9px] uppercase block mb-2">{group}</span>
                                    <div className="flex flex-col gap-1">
                                        {skills.map((skillObj: any) => {
                                            const isSelected = selection?.skill === skillObj.skill;
                                            return (
                                                <div key={skillObj.skill} className="group relative">
                                                    <button
                                                        onClick={() => toggleSkill(group, skillObj.skill)}
                                                        className={`w-full text-left text-[11px] p-1 px-2 flex justify-between items-center transition-colors border ${isSelected ? 'border-yellow-900 bg-yellow-950/30' : 'border-zinc-800 hover:border-zinc-600'}`}
                                                    >
                                                        <span className={isSelected ? 'text-yellow-500 font-bold' : 'text-zinc-400'}>{skillObj.skill}</span>
                                                        {isSelected && (
                                                            <span className={`text-[9px] px-1 rounded ${selection.lead === 'Body' ? 'bg-red-900 text-red-100' : 'bg-blue-900 text-blue-100'}`}>
                                                                {selection.lead}
                                                            </span>
                                                        )}
                                                    </button>
                                                    <div className="hidden group-hover:block absolute z-20 left-full top-0 ml-2 p-2 bg-zinc-800 border border-zinc-600 text-[10px] w-48 shadow-2xl rounded">
                                                        <p className="text-yellow-500 font-bold mb-1">{skillObj.skill}</p>
                                                        <p className="text-zinc-500 text-[9px] mb-1 italic">Stats: {skillObj.stat_pair}</p>
                                                        {skillObj.effect}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* SCHOOLS OF POWER */}
                <div className="bg-black p-4 border border-zinc-800">
                    <h2 className="text-purple-500 font-bold uppercase mb-4 text-xs tracking-widest border-l-2 border-purple-600 pl-2 flex justify-between">
                        <span>Schools of Power</span>
                        <span className={`text-[10px] ${selectedSpells.length >= 2 ? 'text-zinc-300' : 'text-zinc-500'}`}>
                            {selectedSpells.length}/2 Spells
                        </span>
                    </h2>
                    <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                        {Object.entries(schoolsData).map(([statName, data]: [string, any]) => {
                            const statValue = (currentStats as any)[statName.toLowerCase()] || 0;
                            const isLocked = statValue < 12;
                            return (
                                <div key={statName} className={`p-2 border ${isLocked ? 'border-zinc-900 opacity-30 grayscale' : 'border-zinc-800 bg-zinc-900'}`}>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className={`font-bold text-[9px] ${isLocked ? 'text-zinc-500' : 'text-purple-400'}`}>
                                            {data.school}
                                        </span>
                                        <span className="text-[8px] text-zinc-600">{statValue}</span>
                                    </div>
                                    <div className="space-y-1">
                                        {!isLocked && data.spells.map((spell: string) => (
                                            <button
                                                key={spell}
                                                onClick={() => toggleSpell(spell)}
                                                className={`w-full text-left text-[9px] p-1 px-2 border ${selectedSpells.includes(spell) ? 'bg-purple-900 border-purple-500 text-white' : 'bg-black border-zinc-800 text-zinc-500'}`}
                                            >
                                                {spell}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <button
                    onClick={calculateCharacter} disabled={isCalculating}
                    className="w-full bg-yellow-600 hover:bg-yellow-500 disabled:bg-zinc-800 text-black font-bold py-4 uppercase tracking-[0.2em] transition-all shadow-lg active:scale-95"
                >
                    {isCalculating ? "Weaving Soul Strands..." : "Finalize Species Origin"}
                </button>
            </div>

            {/* RIGHT PANEL: COMPILED SHEET */}
            <div className="w-1/2 overflow-y-auto p-8 bg-black custom-scrollbar shadow-inner">
                {compiledData ? (
                    <div className="space-y-8 animate-fade-in">
                        <div className="border-b border-zinc-800 pb-4">
                            <h2 className="text-4xl font-black text-white uppercase tracking-tighter italic">{compiledData.name}</h2>
                            <div className="flex gap-4 mt-2">
                                <span className="text-yellow-500 font-bold bg-yellow-950/20 px-2 py-0.5 border border-yellow-900 text-[10px]">{compiledData.evolutions?.species_base}</span>
                                <span className="text-zinc-500 text-[10px] uppercase py-0.5">Soul Fork v2.4</span>
                            </div>
                        </div>

                        {/* POOLS */}
                        <div className="grid grid-cols-4 gap-2">
                            {[
                                { l: 'HP', v: compiledData.vitals?.max_hp, c: 'text-red-500', b: 'border-red-900/50' },
                                { l: 'SP', v: compiledData.vitals?.max_stamina, c: 'text-orange-500', b: 'border-orange-900/50' },
                                { l: 'CMP', v: compiledData.vitals?.max_composure, c: 'text-blue-500', b: 'border-blue-900/50' },
                                { l: 'FOC', v: compiledData.vitals?.max_focus, c: 'text-purple-500', b: 'border-purple-900/50' }
                            ].map(p => (
                                <div key={p.l} className={`bg-zinc-950 border ${p.b} p-2 text-center shadow-lg`}>
                                    <div className={`${p.c} text-[8px] font-black uppercase tracking-widest`}>{p.l}</div>
                                    <div className="text-xl text-white font-black">{p.v}</div>
                                </div>
                            ))}
                        </div>

                        {/* FINAL ATTRIBUTES */}
                        <div className="bg-zinc-950 border border-zinc-800 p-4 shadow-xl">
                            <h3 className="text-[10px] text-zinc-500 uppercase mb-3 text-center tracking-[0.3em]">Finalized Attributes</h3>
                            <div className="grid grid-cols-6 gap-2">
                                {Object.entries(compiledData.attributes || {}).map(([s, v]: [string, any]) => (
                                    <div key={s} className="text-center group">
                                        <div className="text-[8px] text-zinc-600 uppercase group-hover:text-yellow-600 transition-colors">{s.slice(0, 3)}</div>
                                        <div className="text-lg text-white font-bold">{v}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* SKILLS */}
                        <div>
                            <h3 className="text-yellow-500 font-bold text-xs uppercase border-b border-zinc-800 pb-2 mb-4 tracking-widest">Learned Aptitudes</h3>
                            <div className="grid grid-cols-3 gap-3">
                                {Object.entries(compiledData.tactical_skills).map(([skill, data]: [string, any]) => (
                                    <div key={skill} className="bg-zinc-900/40 p-2 border border-zinc-800 shadow-md">
                                        <div className="text-white font-bold text-[10px] uppercase truncate">{skill}</div>
                                        <div className="flex justify-between items-end mt-1">
                                            <span className="text-[9px] text-zinc-500">Rank {data.rank}</span>
                                            <div className="flex gap-0.5">
                                                {[...Array(4)].map((_, i) => (
                                                    <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < data.pips ? 'bg-yellow-500' : 'bg-zinc-800'}`}></div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* POWERS */}
                        {compiledData.powers?.length > 0 && (
                            <div>
                                <h3 className="text-purple-500 font-bold text-xs uppercase border-b border-zinc-800 pb-2 mb-4 tracking-widest">Manifested Spells</h3>
                                <div className="grid grid-cols-2 gap-3">
                                    {compiledData.powers.map((power: any, idx: number) => (
                                        <div key={idx} className="bg-purple-900/10 p-3 border border-purple-900/30">
                                            <div className="text-white font-bold text-xs uppercase">{power.name}</div>
                                            <div className="text-[9px] text-purple-600 mt-1 uppercase tracking-tighter">School: {power.school}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* EVOLUTIONS */}
                        <div>
                            <h3 className="text-zinc-400 font-bold text-xs uppercase border-b border-zinc-800 pb-2 mb-4 tracking-widest">Biological Manifests</h3>
                            <div className="grid grid-cols-2 gap-2">
                                {compiledData.passives?.map((p: any, idx: number) => (
                                    <div key={idx} className="bg-zinc-950 p-2 border border-zinc-900 group hover:border-zinc-700 transition-colors shadow-sm">
                                        <div className="text-zinc-200 font-bold text-[9px] uppercase group-hover:text-white transition-colors">{p.name}</div>
                                        <div className="text-[9px] text-zinc-600 mt-1 leading-tight">{p.effect}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* INITIALIZE BUTTON */}
                        <div className="mt-8 pt-4 border-t border-zinc-800 flex justify-end">
                            <button
                                onClick={() => {
                                    useCharacterStore.getState().setCharacterSheet(compiledData);
                                    // For now, exit back to main menu. The user can then enter the VTT.
                                    useGameStore.getState().setScreen('MAIN_MENU');
                                }}
                                className="bg-yellow-600 hover:bg-yellow-500 text-black font-bold uppercase text-xs tracking-widest px-8 py-3 shadow-[0_0_15px_rgba(202,138,4,0.3)] transition-all hover:shadow-[0_0_25px_rgba(202,138,4,0.6)]"
                            >
                                Finalize & Exit
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-800">
                        <div className="w-16 h-16 border-4 border-zinc-900 border-t-yellow-900 rounded-full animate-spin mb-4"></div>
                        <p className="text-[10px] uppercase tracking-[0.5em] animate-pulse">Awaiting Soul Resonance</p>
                    </div>
                )}
            </div>
        </div>
    );
};
