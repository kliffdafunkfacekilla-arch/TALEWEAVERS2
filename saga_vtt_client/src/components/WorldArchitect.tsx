import { useState, useEffect } from 'react';
import { useGameStore } from '../store/useGameStore';
import { MapRenderer } from './MapRenderer';

interface WorldArchitectProps {
    onBack: () => void;
}

export function WorldArchitect({ onBack }: WorldArchitectProps) {
    const setWorldData = useGameStore((s: any) => s.setWorldData);
    const selectedHex = useGameStore((s: any) => s.selectedHex);

    // THE MAP LENSES
    const viewLens = useGameStore((s: any) => s.viewLens);
    const setViewLens = useGameStore((s: any) => s.setViewLens);

    const [activeTab, setActiveTab] = useState<'PAINTING' | 'LORE' | 'GEOGRAPHY' | 'CLIMATE' | 'BIOMES' | 'RESOURCES' | 'ECOSYSTEM' | 'FACTIONS'>('PAINTING');
    const [isGenerating, setIsGenerating] = useState(false);

    // --- LORE VAULT STATE ---
    const [loreOnline, setLoreOnline] = useState(false);
    const architectUrl = import.meta.env.VITE_SAGA_ARCHITECT_URL || 'http://localhost:8013';
    const [vaultPath, setVaultPath] = useState("../test_vault");
    const [loreQuery, setLoreQuery] = useState("Aggressive factions that use iron");
    const [loreResults, setLoreResults] = useState<{ title: string; category: string; content: string; distance: number }[]>([]);
    const [isLoreProcessing, setIsLoreProcessing] = useState(false);
    const [loreFactions, setLoreFactions] = useState<{ title: string }[]>([]);
    const [loreWildlife, setLoreWildlife] = useState<{ title: string }[]>([]);
    const [loreResources, setLoreResources] = useState<{ title: string }[]>([]);


    // --- ARCHITECT'S PALETTE (EDIT MODE) ---
    // --- ARCHITECT'S PALETTE (EDIT MODE) ---
    const editMode = useGameStore((s: any) => s.editMode);
    const setEditMode = useGameStore((s: any) => s.setEditMode);
    const activeBrush = useGameStore((s: any) => s.activeBrush);
    const setActiveBrush = useGameStore((s: any) => s.setActiveBrush);
    const brushSize = useGameStore((s: any) => s.brushSize);
    const setBrushSize = useGameStore((s: any) => s.setBrushSize);
    const brushStrength = useGameStore((s: any) => s.brushStrength);
    const setBrushStrength = useGameStore((s: any) => s.setBrushStrength);

    // --- 1. GEOGRAPHY STATE ---
    const [hexCount, setHexCount] = useState(2500);
    const [plateCount, setPlateCount] = useState(15);
    const [heightmap, setHeightmap] = useState("");
    const [heightmapSteps, setHeightmapSteps] = useState([
        { tool: "Hill", count: 200, height: 0.15, range_x: [0.0, 1.0], range_y: [0.0, 1.0] },
        { tool: "Range", count: 10, height: 0.40, range_x: [0.1, 0.9], range_y: [0.1, 0.9] },
        { tool: "Pit", count: 50, height: 0.10, range_x: [0.0, 1.0], range_y: [0.0, 1.0] },
        { tool: "Smooth", count: 2, height: 0.0, range_x: [0.0, 1.0], range_y: [0.0, 1.0] }
    ]);

    // --- 2. CLIMATE STATE ---
    const [rainMultiplier, setRainMultiplier] = useState(1.0);
    const [northPole, setNorthPole] = useState<[number | string, number | string]>([-60, -20]);
    const [equator, setEquator] = useState<[number | string, number | string]>([20, 45]);
    const [southPole, setSouthPole] = useState<[number | string, number | string]>([-70, -30]);
    const [windBands, setWindBands] = useState(["E", "NE", "W", "E", "W", "SE", "E"]);

    // --- 3. BIOME & RESOURCE STATE ---
    const [biomes, setBiomes] = useState([
        { name: "DEEP_TUNDRA", min_temp: -80.0, max_temp: -5.0, min_rain: 0.0, max_rain: 1.0 },
        { name: "SCORCHED_DESERT", min_temp: 30.0, max_temp: 60.0, min_rain: 0.0, max_rain: 0.3 },
        { name: "LUSH_JUNGLE", min_temp: 20.0, max_temp: 50.0, min_rain: 0.7, max_rain: 1.0 },
        { name: "MUSHROOM_SWAMP", min_temp: 10.0, max_temp: 40.0, min_rain: 0.6, max_rain: 1.0 }
    ]);
    const [resources, setResources] = useState([
        { name: "Iron", scarcity: 0.3, is_infinite: false },
        { name: "Wood", scarcity: 0.8, is_infinite: true },
        { name: "Aetherium", scarcity: 0.05, is_infinite: false }
    ]);

    // --- 4. ECOSYSTEM STATE ---
    const [lifeforms, setLifeforms] = useState([
        { name: "Frost Troll", type: "FAUNA", is_aggressive: true, is_farmable: false, is_tameable: false, farm_yield_resource: "Hide", farm_yield_amount: 10, min_temp: -80, max_temp: 0, min_water: 0.0, max_water: 1.0, spawn_chance: 0.05, allowed_biomes: ["DEEP_TUNDRA"], diet: ["Meat"] },
        { name: "Sand Cactus", type: "FLORA", is_aggressive: false, is_farmable: true, is_tameable: false, farm_yield_resource: "Water", farm_yield_amount: 50, min_temp: 30, max_temp: 80, min_water: 0.0, max_water: 0.3, spawn_chance: 0.40, allowed_biomes: ["SCORCHED_DESERT"], diet: ["Sunlight"] }
    ]);

    // --- 5. FACTION STATE ---
    const [factions, setFactions] = useState([
        {
            name: "The_Rot_Coven", aggression: 0.9, expansion_rate: 0.6, will_fight: true, will_farm: false, will_mine: true, will_hunt: true, will_trade: false, base_trade_value: 0.5,
            loved_resources: ["Bones", "Swamp_Gas"], hated_resources: ["Iron"], required_resources: ["Swamp_Gas"], preferred_biomes: ["MUSHROOM_SWAMP"], building_preferences: ["Bone_Hut"]
        }
    ]);

    const fetchLoreEntities = async () => {
        try {
            const res = await fetch(`${architectUrl}/api/lore/entities`);
            if (res.ok) {
                const data = await res.json();
                setLoreFactions(data.factions || []);
                setLoreWildlife(data.wildlife || []);
                setLoreResources(data.resources || []);
            }
        } catch (e) {
            console.error("Failed to fetch lore entities", e);
        }
    };

    // Check if Architect is running on mount
    useEffect(() => {
        fetch(`${architectUrl}/health`)
            .then(res => res.json())
            .then(() => {
                setLoreOnline(true);
                fetchLoreEntities();
            })
            .catch(() => setLoreOnline(false));
    }, []);

    const handleIngestLore = async () => {
        setIsLoreProcessing(true);
        try {
            const res = await fetch(`${architectUrl}/api/lore/ingest`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ vault_path: vaultPath, force_rebuild: true })
            });
            const data = await res.json();
            alert(`Lore Vault Ingested! Processed ${data.files_processed} Markdown files.`);
            fetchLoreEntities(); // Refresh the datalists with new vault output!
        } catch {
            alert("Failed to reach Architect Module.");
        } finally {
            setIsLoreProcessing(false);
        }
    };

    const handleSearchLore = async () => {
        setIsLoreProcessing(true);
        try {
            const res = await fetch(`${architectUrl}/api/lore/search`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: loreQuery, top_k: 3, filter_categories: [] })
            });
            const data = await res.json();
            setLoreResults(data.results || []);
        } catch {
            alert("Search failed. Is Architect Module running?");
        } finally {
            setIsLoreProcessing(false);
        }
    };

    // Helper for inputs that use datalists to append rather than overwrite
    const appendToListString = (currentVal: string[], newVal: string, dataListId: string) => {
        const datalist = document.getElementById(dataListId) as HTMLDataListElement | null;
        if (!datalist) return newVal.split(',').map(s => s.trim()).filter(s => s);

        const options = Array.from(datalist.options).map(o => o.value);

        if (options.includes(newVal)) {
            if (!currentVal.includes(newVal)) return [...currentVal, newVal];
            return currentVal;
        }

        return newVal.split(',').map(s => s.trim()).filter(s => s);
    };

    const handleGenerate = async () => {
        setIsGenerating(true);

        const payload = {
            world_settings: {
                num_hexes: hexCount,
                tectonic_plates: plateCount,
                heightmap_image: heightmap,
                heightmap_steps: heightmapSteps
            },
            climate: {
                north_pole: northPole.map(n => Number(n) || 0),
                equator: equator.map(n => Number(n) || 0),
                south_pole: southPole.map(n => Number(n) || 0),
                rainfall_multiplier: rainMultiplier,
                wind_bands: windBands
            },
            biomes: biomes,
            resources: resources,
            flora_fauna: lifeforms,
            factions: factions
        };


        try {
            const response = await fetch("http://localhost:8002/api/world/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error("C++ Engine Error");
            const result = await response.json();
            setWorldData(result.world_data);
            console.log("[VTT] God Engine Simulation Complete. Saved to Zustand.");
        } catch (err) {
            console.error("API Call failed:", err);
            alert("Failed to reach Python Wrapper on Port 8012. Is saga_architect running?");
        } finally {
            setIsGenerating(false);
        }
    };

    const updateWindBand = (index: number, val: string) => {
        const newBands = [...windBands];
        newBands[index] = val;
        setWindBands(newBands);
    };

    const updateResource = (index: number, field: string, value: any) => {
        const newList = [...resources];
        newList[index] = { ...newList[index], [field]: value };
        setResources(newList);
    };

    const updateBiome = (index: number, field: string, value: any) => {
        const newList = [...biomes];
        newList[index] = { ...newList[index], [field]: value };
        setBiomes(newList);
    };

    const updateLifeform = (index: number, field: string, value: any) => {
        const newList = [...lifeforms];
        newList[index] = { ...newList[index], [field]: value };
        setLifeforms(newList);
    };

    const updateFaction = (index: number, field: string, value: any) => {
        const newList = [...factions];
        newList[index] = { ...newList[index], [field]: value };
        setFactions(newList);
    };

    const updateHeightmapStep = (index: number, field: string, value: any) => {
        const newList = [...heightmapSteps];
        newList[index] = { ...newList[index], [field]: value };
        setHeightmapSteps(newList);
    };

    return (
        <div className="w-full h-full flex bg-zinc-950 text-white font-sans overflow-hidden">
            <datalist id="lore-factions">
                {loreFactions.map((f, idx) => <option key={idx} value={f.title} />)}
            </datalist>
            <datalist id="lore-wildlife">
                {loreWildlife.map((w, idx) => <option key={idx} value={w.title} />)}
            </datalist>
            <datalist id="lore-resources">
                {loreResources.map((r, idx) => <option key={idx} value={r.title} />)}
            </datalist>

            {/* LEFT PANEL: God Engine Config */}
            <div className="w-[400px] bg-zinc-900/90 border-r border-zinc-800 flex flex-col shadow-2xl z-10">

                {/* Header */}
                <div className="p-4 border-b border-zinc-800">
                    <button onClick={onBack} className="text-[10px] text-zinc-500 hover:text-white mb-2 uppercase tracking-widest font-bold">← Return</button>
                    <h1 className="text-xl font-bold tracking-widest text-zinc-100 uppercase">God Engine Config</h1>
                </div>

                {/* Tabs */}
                <div className="flex flex-wrap border-b border-zinc-800 bg-zinc-950">
                    {(['PAINTING', 'LORE', 'GEOGRAPHY', 'CLIMATE', 'BIOMES', 'RESOURCES', 'ECOSYSTEM', 'FACTIONS'] as const).map(tab => (
                        <button
                            key={tab} onClick={() => setActiveTab(tab)}
                            className={`px-2 py-2 text-[9px] font-bold uppercase tracking-widest transition-colors ${activeTab === tab ? 'text-amber-500 border-b-2 border-amber-500 bg-zinc-900' : 'text-zinc-600 hover:text-zinc-400'}`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                <div className="p-5 overflow-y-auto flex-grow text-xs space-y-6 scrollbar-thin">

                    {/* LORE VAULT TAB */}
                    {activeTab === 'LORE' && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                                <span className="font-bold uppercase tracking-widest text-zinc-400">Module 1: Lore DB</span>
                                <span className={`text-[9px] uppercase tracking-widest font-bold ${loreOnline ? 'text-green-500' : 'text-red-500'}`}>
                                    {loreOnline ? 'ARCHITECT ONLINE' : 'ARCHITECT OFFLINE'}
                                </span>
                            </div>

                            {/* Ingest Section */}
                            <div className="p-4 border border-zinc-800 bg-zinc-950/50 rounded-lg space-y-3">
                                <div className="flex justify-between items-center">
                                    <label className="text-amber-500 font-bold uppercase tracking-widest text-[10px]">1. Sync Obsidian Vault</label>
                                    <span className="text-[9px] text-zinc-500 italic">Enter FULL absolute path</span>
                                </div>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={vaultPath}
                                        onChange={(e) => setVaultPath(e.target.value)}
                                        className="flex-grow bg-zinc-900 border border-zinc-700 p-2 text-white outline-none focus:border-amber-500 font-mono text-[10px] placeholder:text-zinc-700"
                                        placeholder="e.g. C:\Users\Documents\LoreVault"
                                    />
                                    {/* @ts-ignore - webkitdirectory is a non-standard attribute but works in Chrome/Electron */}
                                    <input type="file" webkitdirectory="" directory="" onChange={(e) => {
                                        const path = e.target.files?.[0]?.webkitRelativePath?.split('/')[0];
                                        if (path) {
                                            alert(`Note: Browser security prevents getting the full path. Please type or paste the ABSOLUTE path to '${path}' manually.`);
                                            setVaultPath(path);
                                        }
                                    }} className="hidden" id="vaultPicker" />
                                    <label htmlFor="vaultPicker" className="bg-zinc-800 hover:bg-zinc-700 text-white p-2 px-3 text-[10px] font-bold uppercase cursor-pointer transition-colors border border-zinc-700 flex items-center">Browse</label>
                                </div>
                                <p className="text-[9px] text-zinc-600 leading-relaxed">
                                    <strong className="text-zinc-400">Security Note:</strong> Browsers cannot see your full hardware path. Copy and paste the actual path from your File Explorer for best results.
                                </p>
                                <button
                                    onClick={handleIngestLore}
                                    disabled={isLoreProcessing || !loreOnline}
                                    className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-white uppercase tracking-widest text-[10px] font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {isLoreProcessing ? 'Vectorizing...' : 'Wipe & Ingest Vault'}
                                </button>
                            </div>

                            {/* Search Section */}
                            <div className="p-3 border border-zinc-800 bg-zinc-950">
                                <label className="text-blue-400 font-bold uppercase mb-2 block">2. Query ChromaDB</label>
                                <textarea
                                    value={loreQuery}
                                    onChange={(e) => setLoreQuery(e.target.value)}
                                    rows={2}
                                    className="w-full bg-zinc-900 border border-zinc-700 p-2 text-white outline-none focus:border-blue-500 mb-2 resize-none"
                                    placeholder="e.g., What factions live in the Deep Tundra?"
                                />
                                <button
                                    onClick={handleSearchLore}
                                    disabled={isLoreProcessing || !loreOnline}
                                    className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-white uppercase tracking-widest text-[10px] font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {isLoreProcessing ? 'Searching Vector Space...' : 'Execute Query'}
                                </button>
                            </div>

                            {/* Results Display — uses real SearchResult schema: title, category, content, distance */}
                            {loreResults.length > 0 && (
                                <div className="space-y-2">
                                    <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Vector Search Results</span>
                                    {loreResults.map((res, i) => (
                                        <div key={i} className="p-2 border border-zinc-800 bg-zinc-900/50">
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-amber-500 font-bold text-[10px] uppercase truncate">{res.title}</span>
                                                <span className="text-zinc-500 font-mono text-[9px]">{res.category} | Dist: {res.distance.toFixed(3)}</span>
                                            </div>
                                            <p className="text-zinc-300 text-[10px] leading-relaxed italic border-l-2 border-zinc-700 pl-2">
                                                &ldquo;{res.content}&rdquo;
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* GEOGRAPHY TAB */}
                    {activeTab === 'GEOGRAPHY' && (
                        <div className="space-y-4">
                            <div>
                                <label className="text-zinc-400 font-bold uppercase mb-1 block">Map Resolution: {hexCount} Hexes</label>
                                <input type="range" min="500" max="10000" step="100" value={hexCount} onChange={(e) => setHexCount(Number(e.target.value))} className="w-full accent-amber-500" />
                            </div>

                            <div className="p-3 border border-zinc-800 bg-zinc-950">
                                <label className="text-amber-500 font-bold uppercase mb-2 block">1. Procedural Tectonics</label>
                                <label className="text-zinc-400 block mb-1">Plate Count: {plateCount}</label>
                                <input type="range" min="5" max="50" step="1" value={plateCount} onChange={(e) => setPlateCount(Number(e.target.value))} className="w-full accent-amber-500" />
                            </div>

                            <div className="p-3 border border-zinc-800 bg-zinc-950">
                                <label className="text-amber-500 font-bold uppercase mb-2 block">2. Image Import Override</label>
                                <p className="text-[10px] text-zinc-500 mb-2">Provide a heightmap image to bypass procedural tectonics.</p>
                                <div className="flex gap-2">
                                    <input
                                        type="text" placeholder="Leave blank for procedural" value={heightmap} onChange={(e) => setHeightmap(e.target.value)}
                                        className="flex-grow bg-zinc-900 border border-zinc-700 p-2 text-white outline-none focus:border-amber-500 text-xs"
                                    />
                                    <input type="file" accept="image/png, image/jpeg" onChange={(e) => setHeightmap(e.target.files?.[0]?.name || '')} className="hidden" id="heightmapPicker" />
                                    <label htmlFor="heightmapPicker" className="bg-zinc-800 hover:bg-zinc-700 text-white p-2 px-3 text-[10px] font-bold uppercase cursor-pointer transition-colors border border-zinc-700">Browse</label>
                                </div>
                            </div>

                            <div className="p-3 border border-zinc-800 bg-zinc-950 flex flex-col gap-2">
                                <label className="text-amber-500 font-bold uppercase block">3. Procedural Sculpting Brushes</label>
                                <p className="text-[9px] text-zinc-500 leading-tight">These brushes run cumulatively before climate is simulated. Overrides Tectonics.</p>

                                {heightmapSteps.map((step, i) => (
                                    <div key={i} className="flex flex-col gap-2 border border-zinc-800 p-2 bg-zinc-900/50">
                                        <div className="flex justify-between items-center">
                                            <select
                                                value={step.tool}
                                                onChange={e => updateHeightmapStep(i, 'tool', e.target.value)}
                                                className="bg-black border border-zinc-700 p-1 text-xs text-amber-500 font-bold outline-none uppercase"
                                            >
                                                <option value="Hill">Hill</option>
                                                <option value="Pit">Pit</option>
                                                <option value="Range">Range</option>
                                                <option value="Smooth">Smooth</option>
                                            </select>
                                            <button onClick={() => setHeightmapSteps(heightmapSteps.filter((_, idx) => idx !== i))} className="text-red-500 hover:text-red-400 text-xs font-bold uppercase">Del</button>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] text-zinc-400 w-10">Count</span>
                                            <input type="range" min="1" max="500" value={step.count} onChange={e => updateHeightmapStep(i, 'count', Number(e.target.value))} className="flex-grow h-1 accent-amber-500" />
                                            <span className="text-[10px] w-8 text-right font-mono">{step.count}</span>
                                        </div>

                                        {step.tool !== 'Smooth' && (
                                            <div className="flex items-center gap-2">
                                                <span className="text-[10px] text-zinc-400 w-10">Height</span>
                                                <input type="range" min="0.01" max="1.0" step="0.01" value={step.height} onChange={e => updateHeightmapStep(i, 'height', Number(e.target.value))} className="flex-grow h-1 accent-amber-500" />
                                                <span className="text-[10px] w-8 text-right font-mono">{step.height.toFixed(2)}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                                <button onClick={() => setHeightmapSteps([...heightmapSteps, { tool: "Hill", count: 10, height: 0.2, range_x: [0, 1], range_y: [0, 1] }])} className="w-full border border-dashed border-zinc-700 text-zinc-500 py-1.5 hover:bg-zinc-800 transition-colors text-xs uppercase tracking-wider font-bold mt-2">+ Add Brush</button>
                            </div>
                        </div>
                    )}

                    {/* BIOMES TAB */}
                    {activeTab === 'BIOMES' && (
                        <div className="space-y-4">
                            <label className="text-emerald-500 font-bold uppercase mb-2 block">Custom Biomes</label>
                            {biomes.map((b, i) => (
                                <div key={i} className="p-3 border border-zinc-800 bg-zinc-950 flex flex-col gap-3">
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={b.name}
                                            onChange={e => updateBiome(i, 'name', e.target.value.toUpperCase().replace(/\s+/g, '_'))}
                                            className="w-full bg-zinc-900 border border-zinc-700 p-1.5 text-white text-xs font-bold uppercase"
                                            placeholder="BIOME_NAME"
                                        />
                                        <button onClick={() => setBiomes(biomes.filter((_, idx) => idx !== i))} className="text-zinc-500 hover:text-red-500 font-bold px-2">X</button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div>
                                            <span className="text-zinc-500 block text-[10px] mb-1">Temp Range (°C)</span>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[9px] w-6 text-zinc-500">Min</span>
                                                    <input type="range" min="-100" max="100" value={b.min_temp} onChange={e => updateBiome(i, 'min_temp', Number(e.target.value))} className="flex-grow h-1 bg-zinc-700 appearance-none accent-emerald-500" />
                                                    <span className="text-[9px] w-6 text-right font-mono">{b.min_temp}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[9px] w-6 text-zinc-500">Max</span>
                                                    <input type="range" min="-100" max="100" value={b.max_temp} onChange={e => updateBiome(i, 'max_temp', Number(e.target.value))} className="flex-grow h-1 bg-zinc-700 appearance-none accent-emerald-500" />
                                                    <span className="text-[9px] w-6 text-right font-mono">{b.max_temp}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div>
                                            <span className="text-zinc-500 block text-[10px] mb-1">Rain Range</span>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[9px] w-6 text-zinc-500">Min</span>
                                                    <input type="range" min="0" max="1.5" step="0.05" value={b.min_rain} onChange={e => updateBiome(i, 'min_rain', Number(e.target.value))} className="flex-grow h-1 bg-zinc-700 appearance-none accent-emerald-500" />
                                                    <span className="text-[9px] w-6 text-right font-mono">{b.min_rain.toFixed(2)}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[9px] w-6 text-zinc-500">Max</span>
                                                    <input type="range" min="0" max="1.5" step="0.05" value={b.max_rain} onChange={e => updateBiome(i, 'max_rain', Number(e.target.value))} className="flex-grow h-1 bg-zinc-700 appearance-none accent-emerald-500" />
                                                    <span className="text-[9px] w-6 text-right font-mono">{b.max_rain.toFixed(2)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <button onClick={() => setBiomes([...biomes, { name: "NEW_BIOME", min_temp: 0, max_temp: 20, min_rain: 0.1, max_rain: 0.5 }])} className="w-full border border-dashed border-emerald-800 text-emerald-500 py-2 hover:bg-emerald-900/20 transition-colors text-xs uppercase tracking-wider font-bold">+ Add Biome</button>
                        </div>
                    )}

                    {/* RESOURCES TAB */}
                    {activeTab === 'RESOURCES' && (
                        <div className="space-y-4">
                            <label className="text-yellow-500 font-bold uppercase mb-2 block">Global Resources</label>
                            {resources.map((r, i) => (
                                <div key={i} className="p-3 border border-zinc-800 bg-zinc-950 flex flex-col gap-3">
                                    <div className="flex gap-2">
                                        <div className="flex flex-grow items-center gap-2">
                                            <input
                                                type="text"
                                                list="lore-resources"
                                                value={r.name}
                                                onChange={e => updateResource(i, 'name', e.target.value)}
                                                className="flex-grow bg-zinc-900 border border-zinc-700 p-1.5 text-white text-xs font-bold"
                                                placeholder="Resource Name"
                                            />
                                            <label className="flex items-center gap-1 text-[10px] text-zinc-400 uppercase cursor-pointer">
                                                <input type="checkbox" checked={r.is_infinite} onChange={e => updateResource(i, 'is_infinite', e.target.checked)} className="accent-yellow-500" /> Infinite
                                            </label>
                                        </div>
                                        <button onClick={() => setResources(resources.filter((_, idx) => idx !== i))} className="text-zinc-500 hover:text-red-500 font-bold px-2 border-l border-zinc-800 ml-1">X</button>
                                    </div>
                                    <div>
                                        <span className="text-zinc-500 block text-[10px] mb-1">Scarcity (0 = Rare, 1 = Common)</span>
                                        <input type="range" min="0" max="1" step="0.05" value={r.scarcity} onChange={e => updateResource(i, 'scarcity', Number(e.target.value))} className="w-full accent-yellow-500" />
                                    </div>
                                </div>
                            ))}
                            <button onClick={() => setResources([...resources, { name: "New Resource", scarcity: 0.5, is_infinite: false }])} className="w-full border border-dashed border-yellow-800 text-yellow-500 py-2 hover:bg-yellow-900/20 transition-colors text-xs uppercase tracking-wider font-bold">+ Add Resource</button>
                        </div>
                    )}

                    {/* CLIMATE TAB */}
                    {activeTab === 'CLIMATE' && (
                        <div className="space-y-6">
                            <div>
                                <label className="text-blue-400 font-bold uppercase mb-2 block">Global Base Temperatures (°C)</label>
                                <div className="space-y-3 mb-4">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>North Pole</span> <span className="font-mono text-white text-xs">[{northPole[0]}°C to {northPole[1]}°C]</span></div>
                                        <div className="flex gap-2">
                                            <input type="range" min="-100" max="100" value={northPole[0]} onChange={(e) => setNorthPole([Number(e.target.value), northPole[1]])} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-blue-500" />
                                            <input type="range" min="-100" max="100" value={northPole[1]} onChange={(e) => setNorthPole([northPole[0], Number(e.target.value)])} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-blue-500" />
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>Equator</span> <span className="font-mono text-white text-xs">[{equator[0]}°C to {equator[1]}°C]</span></div>
                                        <div className="flex gap-2">
                                            <input type="range" min="-100" max="100" value={equator[0]} onChange={(e) => setEquator([Number(e.target.value), equator[1]])} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-blue-500" />
                                            <input type="range" min="-100" max="100" value={equator[1]} onChange={(e) => setEquator([equator[0], Number(e.target.value)])} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-blue-500" />
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>South Pole</span> <span className="font-mono text-white text-xs">[{southPole[0]}°C to {southPole[1]}°C]</span></div>
                                        <div className="flex gap-2">
                                            <input type="range" min="-100" max="100" value={southPole[0]} onChange={(e) => setSouthPole([Number(e.target.value), southPole[1]])} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-blue-500" />
                                            <input type="range" min="-100" max="100" value={southPole[1]} onChange={(e) => setSouthPole([southPole[0], Number(e.target.value)])} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-blue-500" />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="text-blue-400 font-bold uppercase mb-2 block">The 7 Wind Latitudes</label>
                                <div className="grid grid-cols-7 gap-1">
                                    {windBands.map((dir, i) => (
                                        <select key={i} value={dir} onChange={(e) => updateWindBand(i, e.target.value)} className="bg-zinc-950 border border-zinc-700 text-[10px] p-1 text-center text-white outline-none">
                                            {["N", "NE", "E", "SE", "S", "SW", "W", "NW"].map(d => <option key={d} value={d}>{d}</option>)}
                                        </select>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="text-blue-400 font-bold uppercase mb-1 block">Global Rainfall (x{rainMultiplier})</label>
                                <input type="range" min="0" max="3" step="0.1" value={rainMultiplier} onChange={(e) => setRainMultiplier(Number(e.target.value))} className="w-full accent-blue-500" />
                            </div>
                        </div>
                    )}

                    {/* ECOSYSTEM TAB */}
                    {activeTab === 'ECOSYSTEM' && (
                        <div className="space-y-4">
                            <label className="text-green-500 font-bold uppercase mb-2 block">Custom Flora / Fauna</label>
                            {lifeforms.map((lf, i) => (
                                <div key={i} className="p-3 border border-zinc-800 bg-zinc-950 flex flex-col gap-2">
                                    <div className="flex gap-2 items-center">
                                        <input
                                            type="text"
                                            list="lore-wildlife"
                                            value={lf.name}
                                            onChange={(e) => updateLifeform(i, 'name', e.target.value)}
                                            className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white text-xs font-bold"
                                        />
                                        <select
                                            value={lf.type}
                                            onChange={(e) => updateLifeform(i, 'type', e.target.value)}
                                            className="w-24 bg-zinc-900 border border-zinc-700 p-1 text-zinc-400 text-xs h-full"
                                        >
                                            <option value="FAUNA">FAUNA</option>
                                            <option value="FLORA">FLORA</option>
                                        </select>
                                        <button onClick={() => setLifeforms(lifeforms.filter((_, idx) => idx !== i))} className="text-zinc-500 hover:text-red-500 font-bold px-2 h-full border-l border-zinc-800">X</button>
                                    </div>
                                    <div className="flex flex-col gap-3 mt-2 mb-2">
                                        <div className="flex flex-col gap-1 w-full text-xs">
                                            <div className="flex justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>Temperature (°C)</span> <span className="text-white font-mono">[{lf.min_temp} to {lf.max_temp}]</span></div>
                                            <div className="flex gap-2 items-center">
                                                <input type="range" min="-100" max="100" value={lf.min_temp} onChange={e => updateLifeform(i, 'min_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-green-500" />
                                                <input type="range" min="-100" max="100" value={lf.max_temp} onChange={e => updateLifeform(i, 'max_temp', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-green-500" />
                                            </div>
                                        </div>
                                        <div className="flex flex-col gap-1 w-full text-xs">
                                            <div className="flex justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>Water Need (0-1.5)</span> <span className="text-white font-mono">[{lf.min_water?.toFixed(2)} to {lf.max_water?.toFixed(2)}]</span></div>
                                            <div className="flex gap-2 items-center">
                                                <input type="range" min="0" max="1.5" step="0.05" value={lf.min_water ?? 0} onChange={e => updateLifeform(i, 'min_water', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-green-500" />
                                                <input type="range" min="0" max="1.5" step="0.05" value={lf.max_water ?? 1} onChange={e => updateLifeform(i, 'max_water', Number(e.target.value))} className="w-1/2 h-1 bg-zinc-700 appearance-none accent-green-500" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs mt-1">
                                        <span className="text-zinc-500 w-12 text-[10px]">Diet:</span>
                                        <input type="text" list="lore-resources" value={(lf.diet || []).join(', ')}
                                            onChange={e => updateLifeform(i, 'diet', appendToListString(lf.diet || [], e.target.value, 'lore-resources'))}
                                            className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" placeholder="Meat, Plants, Sunlight" />
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 mt-1">
                                        <label className="flex items-center gap-2 text-[10px] text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={lf.is_farmable} onChange={e => updateLifeform(i, 'is_farmable', e.target.checked)} className="accent-green-500" /> Farmable
                                        </label>
                                        <label className="flex items-center gap-2 text-[10px] text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={lf.is_tameable} onChange={e => updateLifeform(i, 'is_tameable', e.target.checked)} className="accent-green-500" /> Tameable
                                        </label>
                                    </div>
                                    {lf.is_farmable && (
                                        <div className="flex gap-2 text-xs mt-1">
                                            <input type="text" placeholder="Yield Resource (e.g. Meat)" value={lf.farm_yield_resource || ""} onChange={e => updateLifeform(i, 'farm_yield_resource', e.target.value)} className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" />
                                            <input type="number" placeholder="Amt" value={lf.farm_yield_amount || 0} onChange={e => updateLifeform(i, 'farm_yield_amount', Number(e.target.value))} className="w-16 bg-zinc-900 border border-zinc-700 p-1 text-white text-center" />
                                        </div>
                                    )}
                                    <div className="mt-2 border-t border-zinc-800 pt-2">
                                        <div className="flex justify-between items-center text-[10px] text-zinc-500 mb-1">
                                            <span>Spawn Chance</span>
                                            <span className="text-white font-mono">{(lf.spawn_chance * 100).toFixed(0)}%</span>
                                        </div>
                                        <input type="range" min="0" max="1" step="0.01" value={lf.spawn_chance} onChange={e => updateLifeform(i, 'spawn_chance', Number(e.target.value))} className="w-full h-1 bg-zinc-700 appearance-none accent-green-500" />
                                    </div>
                                </div>
                            ))}
                            <button onClick={() => setLifeforms([...lifeforms, { name: "New Creature", type: "FAUNA", is_aggressive: false, is_farmable: false, is_tameable: false, farm_yield_resource: "Meat", farm_yield_amount: 5, min_temp: 0, max_temp: 30, min_water: 0.1, max_water: 1.0, spawn_chance: 0.1, allowed_biomes: ["ANY"], diet: [] }])} className="w-full border border-dashed border-green-800 text-green-500 py-2 hover:bg-green-900/20 transition-colors text-xs uppercase tracking-wider font-bold">+ Add Lifeform</button>
                        </div>
                    )}

                    {/* FACTIONS TAB */}
                    {activeTab === 'FACTIONS' && (
                        <div className="space-y-4">
                            <label className="text-red-500 font-bold uppercase mb-2 block">Custom Cultures</label>
                            {factions.map((f, i) => (
                                <div key={i} className="p-3 border border-zinc-800 bg-zinc-950 flex flex-col gap-3">
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            list="lore-factions"
                                            value={f.name}
                                            onChange={e => updateFaction(i, 'name', e.target.value)}
                                            className="w-full bg-zinc-900 border border-zinc-700 p-1.5 text-white text-xs font-bold"
                                            placeholder="Faction Name"
                                        />
                                        <button onClick={() => setFactions(factions.filter((_, idx) => idx !== i))} className="text-zinc-500 hover:text-red-500 font-bold px-2">X</button>
                                    </div>

                                    <div className="flex flex-col gap-3 mt-1 mb-2">
                                        <div className="flex flex-col gap-1 w-full text-xs">
                                            <div className="flex justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>Aggression</span> <span className="text-white font-mono">{(f.aggression * 100).toFixed(0)}%</span></div>
                                            <input type="range" step="0.05" min="0" max="1" value={f.aggression} onChange={e => updateFaction(i, 'aggression', Number(e.target.value))} className="w-full h-1 bg-zinc-700 appearance-none accent-red-500" />
                                        </div>

                                        <div className="flex flex-col gap-1 w-full text-xs">
                                            <div className="flex justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>Expansion Rate</span> <span className="text-white font-mono">{((f.expansion_rate ?? 0.5) * 100).toFixed(0)}%</span></div>
                                            <input type="range" step="0.05" min="0" max="1" value={f.expansion_rate ?? 0.5} onChange={e => updateFaction(i, 'expansion_rate', Number(e.target.value))} className="w-full h-1 bg-zinc-700 appearance-none accent-red-500" />
                                        </div>

                                        <div className="flex flex-col gap-1 w-full text-xs">
                                            <div className="flex justify-between text-[10px] text-zinc-400 font-bold uppercase"><span>Base Trade Value</span> <span className="text-white font-mono">x{((f.base_trade_value ?? 1.0)).toFixed(1)}</span></div>
                                            <input type="range" step="0.1" min="0" max="3" value={f.base_trade_value ?? 1.0} onChange={e => updateFaction(i, 'base_trade_value', Number(e.target.value))} className="w-full h-1 bg-zinc-700 appearance-none accent-red-500" />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-5 gap-2 text-[10px] mt-1">
                                        <label className="flex items-center gap-1 text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={f.will_fight} onChange={e => updateFaction(i, 'will_fight', e.target.checked)} className="accent-red-500" /> Fight
                                        </label>
                                        <label className="flex items-center gap-1 text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={f.will_farm} onChange={e => updateFaction(i, 'will_farm', e.target.checked)} className="accent-red-500" /> Farm
                                        </label>
                                        <label className="flex items-center gap-1 text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={f.will_mine} onChange={e => updateFaction(i, 'will_mine', e.target.checked)} className="accent-red-500" /> Mine
                                        </label>
                                        <label className="flex items-center gap-1 text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={f.will_hunt} onChange={e => updateFaction(i, 'will_hunt', e.target.checked)} className="accent-red-500" /> Hunt
                                        </label>
                                        <label className="flex items-center gap-1 text-zinc-400 cursor-pointer">
                                            <input type="checkbox" checked={f.will_trade} onChange={e => updateFaction(i, 'will_trade', e.target.checked)} className="accent-red-500" /> Trade
                                        </label>
                                    </div>

                                    <div className="flex flex-col gap-2 mt-2">
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className="text-zinc-500 w-16 text-[9px] uppercase">Require:</span>
                                            <input type="text" list="lore-resources" value={(f.required_resources || []).join(', ')}
                                                onChange={e => updateFaction(i, 'required_resources', appendToListString(f.required_resources || [], e.target.value, 'lore-resources'))}
                                                className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" placeholder="Stone, Iron" />
                                        </div>
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className="text-green-500 w-16 text-[9px] uppercase">Loves:</span>
                                            <input type="text" list="lore-resources" value={(f.loved_resources || []).join(', ')}
                                                onChange={e => updateFaction(i, 'loved_resources', appendToListString(f.loved_resources || [], e.target.value, 'lore-resources'))}
                                                className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" placeholder="Bones, Wood, etc" />
                                        </div>
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className="text-red-500 w-16 text-[9px] uppercase">Hates:</span>
                                            <input type="text" list="lore-resources" value={(f.hated_resources || []).join(', ')}
                                                onChange={e => updateFaction(i, 'hated_resources', appendToListString(f.hated_resources || [], e.target.value, 'lore-resources'))}
                                                className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" placeholder="Iron, Gold, etc" />
                                        </div>
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className="text-blue-400 w-16 text-[9px] uppercase">Biomes:</span>
                                            <input type="text" list="lore-biomes" value={(f.preferred_biomes || []).join(', ')}
                                                onChange={e => updateFaction(i, 'preferred_biomes', appendToListString(f.preferred_biomes || [], e.target.value, 'lore-biomes'))}
                                                className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" placeholder="DEEP_TUNDRA" />
                                        </div>
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className="text-amber-500 w-16 text-[9px] uppercase">Bldgs:</span>
                                            <input type="text" list="lore-buildings" value={(f.building_preferences || []).join(', ')}
                                                onChange={e => updateFaction(i, 'building_preferences', appendToListString(f.building_preferences || [], e.target.value, 'lore-buildings'))}
                                                className="flex-grow bg-zinc-900 border border-zinc-700 p-1 text-white" placeholder="Wood_Hut, Keep" />
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <button onClick={() => setFactions([...factions, { name: "New_Faction", aggression: 0.5, expansion_rate: 0.5, will_fight: true, will_farm: true, will_mine: false, will_hunt: true, will_trade: true, base_trade_value: 1.0, required_resources: [], loved_resources: ["Wood"], hated_resources: [], preferred_biomes: [], building_preferences: [] }])} className="w-full border border-dashed border-red-800 text-red-500 py-2 hover:bg-red-900/20 transition-colors text-xs uppercase tracking-wider font-bold">+ Add Faction</button>
                        </div>
                    )}

                    {/* PAINTING TAB (The Architect's Palette) */}
                    {activeTab === 'PAINTING' && (
                        <div className="space-y-6">

                            {/* Tools Selection */}
                            <div>
                                <label className="text-amber-500 font-bold uppercase mb-2 block border-b border-zinc-800 pb-1">Editing Tools</label>
                                <div className="grid grid-cols-2 gap-2 mt-2">
                                    {(['NONE', 'ELEVATION', 'BIOME', 'FACTION', 'RESOURCE', 'FAUNA', 'FLORA'] as const).map(mode => (
                                        <button
                                            key={mode}
                                            onClick={() => { setEditMode(mode); setActiveBrush(''); }}
                                            className={`px-2 py-2 text-[10px] font-bold uppercase tracking-widest transition-colors rounded border ${editMode === mode ? 'bg-amber-500 text-black border-amber-500' : 'bg-zinc-950 text-zinc-400 border-zinc-700 hover:text-white hover:border-zinc-500'}`}
                                        >
                                            {mode === 'NONE' ? 'INSPECT' : mode}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Brush Setup */}
                            {editMode !== 'NONE' && (
                                <div className="p-3 border border-amber-900/30 bg-amber-900/10 space-y-4">
                                    <div>
                                        <label className="text-white font-bold uppercase text-[10px] mb-2 flex justify-between">
                                            <span>Brush Size (Radius)</span>
                                            <span className="text-amber-500">{brushSize} Hexes</span>
                                        </label>
                                        <input
                                            type="range" min="1" max="25" step="1"
                                            value={brushSize} onChange={(e) => setBrushSize(Number(e.target.value))}
                                            className="w-full h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-white font-bold uppercase text-[10px] mb-2 flex justify-between">
                                            <span>Brush Strength</span>
                                            <span className="text-amber-500">{brushStrength}%</span>
                                        </label>
                                        <input
                                            type="range" min="10" max="100" step="10"
                                            value={brushStrength} onChange={(e) => setBrushStrength(Number(e.target.value))}
                                            className="w-full h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                        />
                                        <p className="text-[9px] text-zinc-500 mt-1 italic">Limits how many hexes inside the radius are affected.</p>
                                    </div>

                                    {/* Data Picker */}
                                    <div className="pt-2 border-t border-amber-900/30">
                                        {editMode === 'ELEVATION' ? (
                                            <div className="grid grid-cols-3 gap-1">
                                                <button onClick={() => setActiveBrush(0.1)} className={`py-2 text-[9px] font-bold uppercase ${activeBrush === 0.1 ? 'bg-blue-900 text-blue-200 border border-blue-500' : 'bg-zinc-950 text-zinc-500 border border-zinc-800'}`}>TRENCH</button>
                                                <button onClick={() => setActiveBrush(0.3)} className={`py-2 text-[9px] font-bold uppercase ${activeBrush === 0.3 ? 'bg-emerald-900 text-emerald-200 border border-emerald-500' : 'bg-zinc-950 text-zinc-500 border border-zinc-800'}`}>LAND</button>
                                                <button onClick={() => setActiveBrush(0.9)} className={`py-2 text-[9px] font-bold uppercase ${activeBrush === 0.9 ? 'bg-zinc-200 text-zinc-950 border border-zinc-300' : 'bg-zinc-950 text-zinc-500 border border-zinc-800'}`}>PEAK</button>
                                            </div>
                                        ) : (
                                            <>
                                                <label className="text-white font-bold uppercase text-[10px] mb-1 block">Active Paint</label>
                                                <input
                                                    type="text"
                                                    value={activeBrush as string}
                                                    onChange={(e) => setActiveBrush(e.target.value.replace(/\s+/g, '_'))}
                                                    placeholder={`Enter ${editMode} Name`}
                                                    className="w-full bg-zinc-950 border border-amber-900/50 p-2 text-white text-xs outline-none focus:border-amber-500"
                                                />
                                            </>
                                        )}
                                    </div>
                                </div>
                            )}

                        </div>
                    )}
                </div>

                <div className="mt-auto p-4 border-t border-zinc-800 bg-zinc-950">
                    <button onClick={handleGenerate} disabled={isGenerating} className="w-full py-3 bg-amber-600 hover:bg-amber-500 text-black font-bold uppercase tracking-[0.2em] disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                        {isGenerating ? 'Simulating...' : 'Commence Generation'}
                    </button>
                </div>
            </div>

            {/* CENTER: The Map Canvas */}
            <div className="flex-grow relative bg-[#050505] overflow-hidden">
                <MapRenderer />

                {/* --- TOP LEFT: VIEW LENSES --- */}
                <div className="absolute top-4 left-4 flex flex-col space-y-2 z-20">
                    {['PHYSICAL', 'POLITICAL', 'RESOURCE', 'THREAT'].map(lens => (
                        <button
                            key={lens}
                            onClick={() => setViewLens(lens as any)}
                            className={`px-3 py-2 text-[10px] font-bold uppercase tracking-widest border transition-all ${viewLens === lens ? 'bg-amber-600 text-black border-amber-500' : 'bg-zinc-900/80 text-zinc-400 border-zinc-700 hover:text-white'}`}
                        >
                            {lens} LENS
                        </button>
                    ))}
                </div>

                {/* --- TOP LEFT: VIEW LENSES --- */}

                {/* Hex Inspector HUD */}
                {selectedHex && (
                    <div className="absolute top-6 right-6 w-72 bg-zinc-900/95 border border-amber-900/50 p-5 shadow-2xl backdrop-blur-md z-20">
                        <h4 className="text-sm font-bold text-amber-500 uppercase tracking-widest mb-3 border-b border-zinc-800 pb-2 flex justify-between">
                            <span>Hex #{selectedHex.id}</span>
                            <span className="text-zinc-500">[{Math.round(selectedHex.x)}, {Math.round(selectedHex.y)}]</span>
                        </h4>

                        <ul className="text-xs font-mono space-y-2">
                            <li className="flex justify-between"><span className="text-zinc-500">Biome</span><span className="text-white font-bold">{selectedHex.biome_tag || "Unknown"}</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Elevation</span><span className="text-white">{((selectedHex.elevation || 0) * 100).toFixed(1)}%</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Temp</span><span className="text-red-400">{(selectedHex.temperature || 0).toFixed(1)}°C</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Moisture</span><span className="text-blue-400">{((selectedHex.moisture || 0) * 100).toFixed(0)}%</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Wind</span><span className="text-zinc-300">[{(selectedHex.wind_dx || 0).toFixed(1)}, {(selectedHex.wind_dy || 0).toFixed(1)}]</span></li>
                        </ul>

                        <div className="mt-4 pt-3 border-t border-zinc-800 space-y-3">
                            {selectedHex.faction_owner ? (
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase block">Territory</span>
                                    <span className="text-xs font-bold text-red-400">{selectedHex.faction_owner}</span>
                                </div>
                            ) : <span className="text-[10px] text-zinc-600 uppercase italic block mb-2">Unclaimed Territory</span>}

                            {selectedHex.local_fauna?.length > 0 && (
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase block mb-1">Local Fauna</span>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedHex.local_fauna.map((lf: string) => (
                                            <span key={lf} className="px-2 py-1 bg-zinc-950 border border-zinc-800 text-[10px] text-red-400">{lf}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {selectedHex.local_flora?.length > 0 && (
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase block mb-1 mt-2">Local Flora</span>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedHex.local_flora.map((lf: string) => (
                                            <span key={lf} className="px-2 py-1 bg-zinc-950 border border-zinc-800 text-[10px] text-green-400">{lf}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {selectedHex.local_resources?.length > 0 && (
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase block mb-1 mt-2">Natural Resources</span>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedHex.local_resources.map((lf: string) => (
                                            <span key={lf} className="px-2 py-1 bg-zinc-950 border border-amber-900/40 text-[10px] text-yellow-500">{lf}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* RIGHT PANEL: Deprecated Editors */}
            <div className="w-[350px] bg-zinc-900/90 border-l border-zinc-800 flex flex-col shadow-2xl z-10 flex-shrink-0">
                <div className="flex-1 overflow-hidden flex flex-col p-8 text-zinc-500 text-center uppercase tracking-widest leading-loose">
                    [Module Offline]<br />
                    Entities & Rules are now handled directly via LLM Backend Pipelines.
                </div>
            </div>
        </div>
    );
}
