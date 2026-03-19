import React, { useState, useMemo, useEffect } from 'react';
import { useGameStore } from '../store/useGameStore';
import { useCharacterStore } from '../store/useCharacterStore';
import { BackstoryPrompts, HERITAGE_TERMINOLOGY, HERITAGE_SLOTS } from '../data/backstory_prompts';
import speciesSlots from '../data/Species_Slots.json';
import speciesBases from '../data/species_base_stats.json';
import evolutionMatrix from '../data/Evolution_Matrix.json';
import tacticalTriads from '../data/tactical_triads.json';
import schoolsData from '../data/schools_of_power.json';
import { generateLoadoutFromSheet } from '../utils/loadoutMapper';

export const SoulweaveWizard: React.FC = () => {
    const setScreen = useGameStore((s) => s.setScreen);
    const setCharacterSheet = useCharacterStore((s) => s.setCharacterSheet);
    const setClientLoadout = useGameStore((s) => s.setClientLoadout);

    // --- Wizard State ---
    const [step, setStep] = useState(0);
    const [name, setName] = useState('');
    const [species, setSpecies] = useState('MAMMAL');
    const [size, setSize] = useState('Balanced Frame');
    const [ancestry, setAncestry] = useState('Standard');

    // 6 Heritages (Mutations)
    const [evolutions, setEvolutions] = useState<Record<string, string>>({
        head_slot: 'Standard',
        arms_slot: 'Standard',
        legs_slot: 'Standard',
        body_slot: 'Standard',
        skin_slot: 'Standard',
        special_slot: 'Standard'
    });

    // 12 Tactical Skills (Triad -> skill_name)
    const [selectedSkills, setSelectedSkills] = useState<Record<string, string>>({});

    // Schools of Power
    const [primeSchool, setPrimeSchool] = useState<string | null>(null);
    const [auxSchool, setAuxSchool] = useState<string | null>(null);

    // Catalyst & Gear
    const [catalystId, setCatalystId] = useState<string | null>(null);

    const [isCalculating, setIsCalculating] = useState(false);
    const [animFrame, setAnimFrame] = useState(0);

    // Animation Loop
    useEffect(() => {
        const timer = setInterval(() => {
            setAnimFrame(f => (f + 1) % 2);
        }, 400); // 400ms per frame for a steady walk
        return () => clearInterval(timer);
    }, []);

    // --- Mappings & Constants ---
    const spriteMapping: Record<string, { x: number, y: number }> = {
        'MAMMAL': { x: 0, y: 0 },
        'AVIAN': { x: 512, y: 0 },
        'REPTILE': { x: 1024, y: 0 },
        'INSECT': { x: 1536, y: 0 },
        'PLANT': { x: 2048, y: 0 },
        'AQUATIC': { x: 2560, y: 0 }
    };

    const currentSprite = spriteMapping[species] || { x: 0, y: 0 };

    // --- Dynamic Stat Calculation ---
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


        // Mutation bonuses
        const chosenMutations = [...Object.values(evolutions), size, ancestry];
        evolutionMatrix.forEach((trait: any) => {
            if (chosenMutations.includes(trait.name) && trait.name !== "Standard") {
                Object.entries(trait.stats || {}).forEach(([key, val]: [string, any]) => {
                    const potentialStats = key.replace('+', '').split(',').map(s => s.trim().toLowerCase());
                    potentialStats.forEach(ps => {
                        const cleanKey = ps.includes('reflex') ? 'reflexes' : ps.match(/[a-z]+/)?.[0];
                        if (cleanKey && (stats as any).hasOwnProperty(cleanKey)) {
                            const bonus = typeof val === 'number' ? val : 1;
                            (stats as any)[cleanKey] += bonus;
                        }
                    });
                });
            }
        });

        // Skill Lead Bonuses (Automated: Higher stat in pair gets +1)
        Object.keys(selectedSkills).forEach((triadKey: string) => {
            const triadDataArray = (tacticalTriads as any)[triadKey];
            const chosenSkillName = selectedSkills[triadKey];
            const skillData = triadDataArray?.find((s: any) => s.skill === chosenSkillName);

            if (skillData && skillData.stat_pair) {
                const parts = skillData.stat_pair.split(' + ').map((s: string) => s.trim().toLowerCase().replace('reflex', 'reflexes'));
                const statA = parts[0];
                const statB = parts[1];

                // Automate lead: Choose the one that is currently higher
                const leadStat = (stats as any)[statA] >= (stats as any)[statB] ? statA : statB;
                if ((stats as any).hasOwnProperty(leadStat)) (stats as any)[leadStat] += 1;
            }
        });

        return stats;
    }, [species, evolutions, size, ancestry, selectedSkills]);

    // --- Finalization ---
    const finalizeSoul = async () => {
        if (!name) { alert("Your soul must have a name to anchor in the manifest world."); return; }
        setIsCalculating(true);
        try {
            const charEngineUrl = import.meta.env.VITE_SAGA_CHAR_ENGINE_URL || 'http://localhost:8014';
            const catalyst = BackstoryPrompts.catalyst.options.find(o => o.id === catalystId);

            // Map Skills to proficiency gear (Logic: choose best weapon/armor based on skills)
            const skillGear: Record<string, string> = {};
            const selectedSkillNames = Object.values(selectedSkills);

            if (selectedSkillNames.includes('Aggressive') || selectedSkillNames.includes('Dueling')) {
                skillGear['main_hand'] = 'wpn_steel_sword';
            }
            if (selectedSkillNames.includes('Skirmish') || selectedSkillNames.includes('Precise')) {
                skillGear['off_hand'] = 'wpn_hunting_bow';
            }
            if (selectedSkillNames.includes('Rooted') || selectedSkillNames.includes('Impose')) {
                skillGear['body_armor'] = 'arm_iron_plate';
            } else if (selectedSkillNames.includes('Fluid') || selectedSkillNames.includes('Speed')) {
                skillGear['body_armor'] = 'arm_leather_vest';
            }

            const finalLoadout = { ...catalyst?.gear, ...skillGear };

            // Materialize Lead Stats for the engine
            const finalSkills: Record<string, { lead: string }> = {};
            Object.entries(selectedSkills).forEach(([triadKey, skillName]) => {
                const triadDataArray = (tacticalTriads as any)[triadKey];
                const skillData = triadDataArray?.find((s: any) => s.skill === skillName);
                if (skillData && skillData.stat_pair) {
                    const parts = skillData.stat_pair.split(' + ').map((s: string) => s.trim().toLowerCase().replace('reflex', 'reflexes'));
                    const leadStat = (currentStats as any)[parts[0]] >= (currentStats as any)[parts[1]] ? parts[0] : parts[1];
                    finalSkills[skillName] = { lead: leadStat };
                }
            });

            const layers = [
                {
                    sheet_url: animFrame === 0 ? "/assets/species_walk_1.png" : "/assets/species_walk_2.png",
                    x: currentSprite.x, y: currentSprite.y, w: 512, h: 512
                }
            ];

            const response = await fetch(`${charEngineUrl}/api/rules/character/calculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    base_attributes: null,
                    evolutions: { species_base: species, size_slot: size, ancestry_slot: ancestry, ...evolutions },
                    tactical_skills: finalSkills,
                    selected_powers: [
                        primeSchool ? { name: schoolsData[primeSchool as keyof typeof schoolsData].tiers["1"].OFFENSE.name } : null,
                        auxSchool ? { name: schoolsData[auxSchool as keyof typeof schoolsData].tiers["1"].UTILITY.name } : null
                    ].filter(p => p !== null),
                    equipped_loadout: finalLoadout,
                    composite_sprite: { layers }
                })
            });

            if (response.ok) {
                const fullSheet = await response.json();
                setCharacterSheet(fullSheet);
                setClientLoadout(generateLoadoutFromSheet(fullSheet));
                setScreen('PLAYER');
            } else {
                alert("The Soulweave collapsed. (Character Engine Error)");
            }
        } catch (err) {
            alert("Critical Aetheric Failure. Check connection to Character Engine.");
        } finally {
            setIsCalculating(false);
        }
    };

    // --- Navigation ---
    const totalSteps = 25;
    const progress = (step / (totalSteps - 1)) * 100;

    const next = () => setStep(s => Math.min(s + 1, totalSteps - 1));
    const back = () => setStep(s => Math.max(s - 1, 0));

    // --- Renderers ---

    const renderHeader = () => (
        <div className="w-full flex flex-col items-center py-8">
            <h1 className="text-3xl font-black tracking-[0.3em] text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-500 to-amber-800 uppercase animate-pulse">
                Soulweave Origin
            </h1>
            <div className="w-[600px] h-1 bg-zinc-900 mt-4 relative overflow-hidden rounded-full">
                <div
                    className="absolute inset-0 bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-700 ease-out shadow-[0_0_15px_rgba(245,158,11,0.5)]"
                    style={{ width: `${progress}%` }}
                />
            </div>
            <div className="flex gap-16 mt-2 text-[10px] uppercase font-bold text-zinc-600 tracking-widest">
                <span className={step < 3 ? 'text-amber-500' : ''}>I. Manifestation</span>
                <span className={step >= 3 && step < 9 ? 'text-amber-500' : ''}>II. Heritage</span>
                <span className={step >= 9 && step < 23 ? 'text-amber-500' : ''}>III. Weaving</span>
                <span className={step >= 23 ? 'text-amber-500' : ''}>IV. Materialization</span>
            </div>
        </div>
    );

    const renderSpecies = () => (
        <div className="flex flex-col items-center gap-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xl font-bold text-zinc-200 uppercase tracking-widest text-center max-w-2xl px-8 leading-relaxed">
                {BackstoryPrompts.species.question}
            </h2>
            <div className="flex gap-6">
                {BackstoryPrompts.species.options.map((opt) => (
                    <button
                        key={opt.id}
                        onClick={() => { setSpecies(opt.id); next(); }}
                        className={`group p-6 border-2 transition-all flex flex-col items-center w-40 h-56 bg-zinc-950/50 hover:bg-amber-950/20 active:scale-95 ${species === opt.id ? 'border-amber-500 shadow-[0_0_30px_rgba(245,158,11,0.2)]' : 'border-zinc-800'}`}
                    >
                        <div className="w-20 h-20 mb-6 flex items-center justify-center grayscale group-hover:grayscale-0 transition-all duration-500">
                            <div
                                style={{
                                    width: '32px',
                                    height: '32px',
                                    backgroundImage: 'url(/assets/species.png)',
                                    backgroundPosition: `-${spriteMapping[opt.id].x / 16}px 0px`,
                                    backgroundSize: `${3072 / 16}px auto`,
                                    imageRendering: 'pixelated',
                                    transform: 'scale(4)'
                                }}
                            />
                        </div>
                        <span className="text-sm font-black uppercase text-zinc-400 group-hover:text-amber-400 tracking-widest">{opt.label}</span>
                        <p className="text-[10px] text-zinc-600 mt-4 leading-tight opacity-0 group-hover:opacity-100 transition-opacity">{opt.description}</p>
                    </button>
                ))}
            </div>
        </div>
    );

    const renderSimpleChoice = (title: string, currentVal: string, setVal: (v: string) => void, options: string[]) => (
        <div className="flex flex-col items-center gap-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xl font-bold text-zinc-200 uppercase tracking-widest text-center max-w-2xl px-8 leading-relaxed">
                {title}
            </h2>
            <div className="grid grid-cols-3 gap-4 w-[800px]">
                {options.map((opt) => (
                    <button
                        key={opt}
                        onClick={() => { setVal(opt); next(); }}
                        className={`p-4 border text-sm font-bold uppercase transition-all hover:bg-zinc-900 active:scale-95 ${currentVal === opt ? 'border-amber-500 bg-amber-900/10 text-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.1)]' : 'border-zinc-800'}`}
                    >
                        {opt}
                    </button>
                ))}
            </div>
            <button onClick={back} className="text-zinc-600 hover:text-white uppercase text-[10px] font-bold tracking-widest mt-8">← Previous Strand</button>
        </div>
    );

    const renderHeritageScreen = (heritageIdx: number) => {
        const slot = HERITAGE_SLOTS[heritageIdx];
        const currentTrait = evolutions[slot];
        const speciesTerms = HERITAGE_TERMINOLOGY[species] || HERITAGE_TERMINOLOGY.MAMMAL;
        const term = speciesTerms[heritageIdx];
        const options = (speciesSlots as any)[species]?.[slot] || ["Standard"];
        const promptsForSpecies = (BackstoryPrompts.heritages as any)[species] || BackstoryPrompts.heritages.DEFAULT;
        const question = promptsForSpecies.questions[heritageIdx];

        return (
            <div className="flex flex-col items-center gap-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex flex-col items-center">
                    <span className="text-amber-600 text-[10px] font-black uppercase tracking-[0.5em] mb-2">{term} Heritage</span>
                    <h2 className="text-xl font-bold text-zinc-200 uppercase tracking-widest text-center max-w-2xl px-8 leading-relaxed">
                        {question}
                    </h2>
                </div>
                <div className="grid grid-cols-3 gap-3 w-[900px]">
                    {options.map((opt: string) => {
                        const traitData = evolutionMatrix.find((t: any) => t.name === opt);
                        const effect = (traitData?.passives?.[0] as any)?.effect || (traitData as any)?.effect || "No aetheric data available.";
                        return (
                            <button
                                key={opt}
                                onClick={() => { setEvolutions({ ...evolutions, [slot]: opt }); next(); }}
                                className={`group p-4 border text-left flex flex-col gap-2 transition-all hover:bg-zinc-900 active:scale-[0.98] ${currentTrait === opt ? 'border-amber-500 bg-amber-900/10' : 'border-zinc-800'}`}
                            >
                                <span className={`text-[11px] font-black uppercase ${currentTrait === opt ? 'text-amber-400' : 'text-zinc-400 group-hover:text-white'}`}>{opt}</span>
                                <p className="text-[9px] text-zinc-600 leading-tight group-hover:text-zinc-400 transition-colors uppercase italic">{effect}</p>
                            </button>
                        );
                    })}
                </div>
                <button onClick={back} className="text-zinc-600 hover:text-white uppercase text-[10px] font-bold tracking-widest mt-4">← Previous Strand</button>
            </div>
        );
    };

    const renderSkillScreen = (triadName: string) => {
        const triad = BackstoryPrompts.triads[triadName as keyof typeof BackstoryPrompts.triads];
        const selection = selectedSkills[triadName];

        return (
            <div className="flex flex-col items-center gap-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex flex-col items-center">
                    <h2 className="text-xl font-bold text-zinc-200 uppercase tracking-widest text-center max-w-2xl px-8 leading-relaxed">
                        {triad.question}
                    </h2>
                </div>
                <div className="flex flex-col gap-4 w-[600px]">
                    {triad.options.map((opt) => (
                        <button
                            key={opt.skill}
                            onClick={() => { setSelectedSkills({ ...selectedSkills, [triadName]: opt.skill }); next(); }}
                            className={`p-5 border text-left transition-all hover:bg-amber-950/10 group ${selection === opt.skill ? 'border-amber-600 bg-amber-950/20 shadow-[0_0_20px_rgba(245,158,11,0.1)]' : 'border-zinc-800'}`}
                        >
                            <span className={`text-xs font-bold block mb-1 uppercase ${selection === opt.skill ? 'text-amber-400' : 'text-zinc-500 group-hover:text-zinc-200'}`}>{opt.label}</span>
                            <span className="text-[9px] text-zinc-700 uppercase tracking-widest italic">{opt.skill} Aptitude</span>
                        </button>
                    ))}
                </div>
                <button onClick={back} className="text-zinc-600 hover:text-white uppercase text-[10px] font-bold tracking-widest mt-4">← Previous Strand</button>
            </div>
        );
    };

    const renderSchoolScreen = (type: 'prime' | 'aux') => {
        const data = BackstoryPrompts.schools[type];
        const current = type === 'prime' ? primeSchool : auxSchool;

        return (
            <div className="flex flex-col items-center gap-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h2 className="text-xl font-bold text-zinc-200 uppercase tracking-widest text-center max-w-2xl px-8 leading-relaxed">
                    {data.question}
                </h2>
                <div className="grid grid-cols-2 gap-4 w-[800px]">
                    {data.options.map((opt) => (
                        <button
                            key={opt.id}
                            disabled={type === 'aux' && opt.id === primeSchool}
                            onClick={() => { if (type === 'prime') setPrimeSchool(opt.id); else setAuxSchool(opt.id); next(); }}
                            className={`p-6 border text-left transition-all hover:bg-purple-950/10 disabled:opacity-30 active:scale-95 ${current === opt.id ? 'border-purple-600 bg-purple-950/20 shadow-[0_0_20px_rgba(147,51,234,0.1)]' : 'border-zinc-800'}`}
                        >
                            <span className={`text-sm font-black uppercase block mb-1 ${current === opt.id ? 'text-purple-400' : 'text-zinc-400'}`}>{opt.label}</span>
                            <p className="text-[10px] text-zinc-600 leading-tight uppercase font-medium">{opt.description}</p>
                        </button>
                    ))}
                </div>
                <button onClick={back} className="text-zinc-600 hover:text-white uppercase text-[10px] font-bold tracking-widest mt-4">← Previous Strand</button>
            </div>
        );
    };

    const renderCatalyst = () => (
        <div className="flex flex-col items-center gap-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xl font-bold text-zinc-200 uppercase tracking-widest text-center max-w-2xl px-8 leading-relaxed">
                {BackstoryPrompts.catalyst.question}
            </h2>
            <div className="flex flex-col gap-4 w-[700px]">
                {BackstoryPrompts.catalyst.options.map((opt) => (
                    <button
                        key={opt.id}
                        onClick={() => { setCatalystId(opt.id); next(); }}
                        className={`p-6 border text-left transition-all hover:bg-amber-950/10 active:scale-[0.99] group ${catalystId === opt.id ? 'border-amber-500 bg-amber-950/20 shadow-[0_0_30px_rgba(245,158,11,0.1)]' : 'border-zinc-800'}`}
                    >
                        <div className="flex justify-between items-center mb-2">
                            <span className={`text-lg font-black uppercase tracking-tight ${catalystId === opt.id ? 'text-amber-400' : 'text-zinc-300'}`}>{opt.label}</span>
                            <div className="flex gap-2">
                                {Object.values(opt.gear).map((item, i) => (
                                    <span key={i} className="text-[8px] bg-zinc-900 border border-zinc-700 px-2 py-0.5 text-zinc-500 uppercase rounded">{item.split('_').pop()}</span>
                                ))}
                            </div>
                        </div>
                        <p className={`text-xs transition-colors ${catalystId === opt.id ? 'text-zinc-200' : 'text-zinc-500 group-hover:text-zinc-400'}`}>{opt.backstory}</p>
                    </button>
                ))}
            </div>
            <button onClick={back} className="text-zinc-600 hover:text-white uppercase text-[10px] font-bold tracking-widest mt-4">← Previous Strand</button>
        </div>
    );

    const renderFinal = () => {
        const catalyst = BackstoryPrompts.catalyst.options.find(o => o.id === catalystId);

        return (
            <div className="flex w-full h-full animate-in fade-in duration-1000">
                {/* Review Panel */}
                <div className="w-2/3 p-12 overflow-y-auto border-r border-zinc-800 space-y-12 bg-black/50 custom-scrollbar">
                    <div className="border-b border-amber-900/50 pb-8">
                        <span className="text-amber-600 text-[10px] font-black uppercase tracking-[0.6em] mb-4 block">The Ancestral Blueprint</span>
                        <div className="flex items-center gap-8">
                            <div className="w-24 h-24 border border-amber-900 bg-amber-950/10 flex items-center justify-center p-4 rounded shadow-[inset_0_0_20px_rgba(0,0,0,0.5)]">
                                <div
                                    style={{
                                        width: '64px',
                                        height: '64px',
                                        backgroundImage: `url(/assets/species_walk_${animFrame + 1}.png)`,
                                        backgroundPosition: `-${currentSprite.x / 8}px 0px`, // Assuming Down-facing walk is first 2 frames
                                        backgroundSize: `${3072 / 8}px auto`,
                                        imageRendering: 'pixelated',
                                        transform: 'scale(1.5)'
                                    }}
                                />
                            </div>
                            <div>
                                <h3 className="text-4xl font-black text-white italic tracking-tighter uppercase">{species} / {ancestry}</h3>
                                <p className="text-sm text-zinc-500 mt-1 uppercase tracking-widest">{size}</p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-12">
                        {/* Attributes */}
                        <div className="space-y-4">
                            <h4 className="text-amber-500 font-bold text-xs uppercase tracking-widest border-b border-zinc-800 pb-2">Innate Attributes</h4>
                            <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                                {Object.entries(currentStats).map(([stat, val]) => (
                                    <div key={stat} className="flex justify-between items-center border-b border-zinc-900/50 py-1">
                                        <span className="text-[10px] text-zinc-600 uppercase font-medium">{stat}</span>
                                        <span className="text-white font-black">{val}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        {/* Summary */}
                        <div className="space-y-4">
                            <h4 className="text-amber-500 font-bold text-xs uppercase tracking-widest border-b border-zinc-800 pb-2">Narrative Core</h4>
                            <div className="text-zinc-400 text-xs italic leading-relaxed space-y-4">
                                <p>{catalyst?.backstory}</p>
                                <p>You have mastered the {primeSchool} as your prime discipline, complemented by the {auxSchool} school.</p>
                                <div className="pt-4 flex flex-wrap gap-2">
                                    {Object.values(selectedSkills).map(skillName => (
                                        <span key={skillName} className="px-2 py-1 bg-zinc-900 border border-zinc-800 text-[8px] uppercase text-zinc-500 font-bold">{skillName}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Final Step Action */}
                <div className="w-1/3 p-12 bg-zinc-950 flex flex-col justify-center items-center gap-12">
                    <div className="w-full space-y-2">
                        <span className="text-[10px] text-zinc-600 uppercase font-black tracking-widest">Seal Your Identity</span>
                        <input
                            type="text"
                            placeholder="NAME YOUR VESSEL..."
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full bg-black border-2 border-amber-900 px-6 py-4 text-white text-xl font-black uppercase tracking-widest outline-none focus:border-amber-500 transition-all placeholder:text-zinc-800 shadow-[0_0_30px_rgba(0,0,0,0.5)]"
                        />
                    </div>

                    <div className="w-full space-y-4">
                        <button
                            disabled={!name || isCalculating}
                            onClick={finalizeSoul}
                            className="w-full bg-gradient-to-b from-amber-400 to-amber-700 hover:from-amber-300 hover:to-amber-600 disabled:from-zinc-800 disabled:to-zinc-900 text-black font-black py-6 uppercase tracking-[0.5em] text-sm transition-all shadow-2xl active:scale-95 disabled:opacity-50"
                        >
                            {isCalculating ? "MATERIALIZING..." : "COMMENCE SOULWEAVE"}
                        </button>
                        <button onClick={back} className="w-full text-zinc-600 hover:text-white uppercase text-[10px] font-bold tracking-widest">← Return to Catalyst</button>
                    </div>
                </div>
            </div>
        );
    }

    // --- Main Wizard Logic ---
    const renderStep = () => {
        if (step === 0) return renderSpecies();
        if (step === 1) return renderSimpleChoice("What is the physical burden of your vessel?", size, setSize, (speciesSlots as any)[species]?.size_slot || ["Standard"]);
        if (step === 2) return renderSimpleChoice("Which ancestral biome does your blood echo?", ancestry, setAncestry, (speciesSlots as any)[species]?.ancestry_slot || ["Standard"]);

        // Biological Heritage (3rd - 8th steps)
        if (step >= 3 && step <= 8) return renderHeritageScreen(step - 3);

        // Tactical Triads (9th - 20th steps)
        const triadKeys = Object.keys(BackstoryPrompts.triads);
        if (step >= 9 && step <= 20) return renderSkillScreen(triadKeys[step - 9]);

        // Schools of Power
        if (step === 21) return renderSchoolScreen('prime');
        if (step === 22) return renderSchoolScreen('aux');

        // Catalyst
        if (step === 23) return renderCatalyst();

        // Final
        if (step === 24) return renderFinal();

        return <div>Out of bounds</div>;
    };

    return (
        <div className="fixed inset-0 bg-black flex flex-col overflow-hidden text-zinc-300 font-sans select-none">
            {step < 24 && renderHeader()}
            <div className="flex-grow flex items-center justify-center relative">
                {renderStep()}
            </div>

            {/* Background Texture / Grain / Grid (Aesthetic) */}
            <div className="fixed inset-0 pointer-events-none z-[-1] opacity-10">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_0%,_black_90%)]" />
                <div className="w-full h-full bg-[url('/assets/ui/noise.png')] opacity-20" />
            </div>
        </div>
    );
};
