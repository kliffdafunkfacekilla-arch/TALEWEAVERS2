import { useState, useEffect } from 'react';
import { useGameStore } from '../store/useGameStore';
import { MapRenderer } from './MapRenderer';

interface WorldArchitectProps {
    onBack: () => void;
}

export function WorldArchitect({ onBack }: WorldArchitectProps) {
    const setWorldData = useGameStore((s) => s.setWorldData);
    const worldData = useGameStore((s) => s.worldData);
    const selectedHex = useGameStore((s) => s.selectedHex);

    const [activeTab, setActiveTab] = useState<'LORE' | 'GEOGRAPHY' | 'CLIMATE' | 'ECOSYSTEM' | 'FACTIONS'>('LORE');
    const [isGenerating, setIsGenerating] = useState(false);

    // --- LORE VAULT STATE (PORT 8001) ---
    const [loreOnline, setLoreOnline] = useState(false);
    const [vaultPath, setVaultPath] = useState("../test_vault");
    const [loreQuery, setLoreQuery] = useState("Aggressive factions that use iron");
    const [loreResults, setLoreResults] = useState<{ title: string; category: string; content: string; distance: number }[]>([]);
    const [isLoreProcessing, setIsLoreProcessing] = useState(false);

    // --- 1. GEOGRAPHY STATE ---
    const [hexCount, setHexCount] = useState(2500);
    const [plateCount, setPlateCount] = useState(15);
    const [heightmap, setHeightmap] = useState("");

    // --- 2. CLIMATE STATE ---
    const [rainMultiplier, setRainMultiplier] = useState(1.0);
    const [northPole, setNorthPole] = useState([-60, -20]);
    const [equator, setEquator] = useState([20, 45]);
    const [southPole, setSouthPole] = useState([-70, -30]);
    const [windBands, setWindBands] = useState(["E", "NE", "W", "E", "W", "SE", "E"]);

    // --- 3. ECOSYSTEM STATE ---
    const [lifeforms, setLifeforms] = useState([
        { name: "Frost Troll", type: "FAUNA", is_aggressive: true, min_temp: -80, max_temp: 0, spawn_chance: 0.05, allowed_biomes: ["DEEP_TUNDRA"] },
        { name: "Sand Cactus", type: "FLORA", is_aggressive: false, min_temp: 30, max_temp: 80, spawn_chance: 0.40, allowed_biomes: ["SCORCHED_DESERT"] }
    ]);

    // --- 4. FACTION STATE ---
    const [factions, setFactions] = useState([
        {
            name: "The_Rot_Coven", aggression: 0.9, will_fight: true, will_farm: false, will_mine: true,
            loved_resources: ["Bones", "Swamp_Gas"], hated_resources: ["Iron"]
        }
    ]);

    // Check if Port 8001 is running on mount
    useEffect(() => {
        fetch("http://localhost:8001/health")
            .then(res => res.json())
            .then(() => setLoreOnline(true))
            .catch(() => setLoreOnline(false));
    }, []);

    const handleIngestLore = async () => {
        setIsLoreProcessing(true);
        try {
            const res = await fetch("http://localhost:8001/api/lore/ingest", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ vault_path: vaultPath, force_rebuild: true })
            });
            const data = await res.json();
            alert(`Lore Vault Ingested! Processed ${data.files_processed} Markdown files.`);
        } catch {
            alert("Failed to reach Lore Module on Port 8001.");
        } finally {
            setIsLoreProcessing(false);
        }
    };

    const handleSearchLore = async () => {
        setIsLoreProcessing(true);
        try {
            const res = await fetch("http://localhost:8001/api/lore/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: loreQuery, top_k: 3, filter_categories: [] })
            });
            const data = await res.json();
            setLoreResults(data.results || []);
        } catch {
            alert("Search failed. Is Port 8001 running?");
        } finally {
            setIsLoreProcessing(false);
        }
    };

    const handleGenerate = async () => {
        setIsGenerating(true);

        const payload = {
            world_settings: {
                num_hexes: hexCount,
                tectonic_plates: plateCount,
                heightmap_image: heightmap
            },
            climate: {
                north_pole: northPole,
                equator: equator,
                south_pole: southPole,
                rainfall_multiplier: rainMultiplier,
                wind_bands: windBands
            },
            biomes: [
                { name: "DEEP_TUNDRA", min_temp: -80.0, max_temp: -5.0, min_rain: 0.0, max_rain: 1.0 },
                { name: "SCORCHED_DESERT", min_temp: 30.0, max_temp: 60.0, min_rain: 0.0, max_rain: 0.3 },
                { name: "LUSH_JUNGLE", min_temp: 20.0, max_temp: 50.0, min_rain: 0.7, max_rain: 1.0 },
                { name: "MUSHROOM_SWAMP", min_temp: 10.0, max_temp: 40.0, min_rain: 0.6, max_rain: 1.0 }
            ],
            flora_fauna: lifeforms,
            factions: factions
        };

        try {
            const response = await fetch("http://localhost:8002/api/world/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (!response.ok) throw new Error("C++ Engine Error");
            const result = await response.json();
            setWorldData(result.world_data);
            console.log("[VTT] God Engine Simulation Complete. Saved to Zustand.");
        } catch (error) {
            console.error("Simulation Failed:", error);
            alert("Failed to reach Python Wrapper on Port 8002. Is saga_architect running?");
        } finally {
            setIsGenerating(false);
        }
    };

    const updateWindBand = (index: number, val: string) => {
        const newBands = [...windBands];
        newBands[index] = val;
        setWindBands(newBands);
    };

    return (
        <div className="w-full h-full flex bg-zinc-950 text-white font-sans overflow-hidden">

            {/* LEFT PANEL: God Engine Config */}
            <div className="w-[400px] bg-zinc-900/90 border-r border-zinc-800 flex flex-col shadow-2xl z-10">

                {/* Header */}
                <div className="p-4 border-b border-zinc-800">
                    <button onClick={onBack} className="text-[10px] text-zinc-500 hover:text-white mb-2 uppercase tracking-widest font-bold">← Return</button>
                    <h1 className="text-xl font-bold tracking-widest text-zinc-100 uppercase">God Engine Config</h1>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-zinc-800 bg-zinc-950">
                    {(['LORE', 'GEOGRAPHY', 'CLIMATE', 'ECOSYSTEM', 'FACTIONS'] as const).map(tab => (
                        <button
                            key={tab} onClick={() => setActiveTab(tab)}
                            className={`flex-1 py-2 text-[9px] font-bold uppercase tracking-widest transition-colors ${activeTab === tab ? 'text-amber-500 border-b-2 border-amber-500 bg-zinc-900' : 'text-zinc-600 hover:text-zinc-400'}`}
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
                                    {loreOnline ? 'PORT 8001 ONLINE' : 'PORT 8001 OFFLINE'}
                                </span>
                            </div>

                            {/* Ingest Section */}
                            <div className="p-3 border border-zinc-800 bg-zinc-950">
                                <label className="text-amber-500 font-bold uppercase mb-2 block">1. Ingest Markdown Vault</label>
                                <input
                                    type="text"
                                    value={vaultPath}
                                    onChange={(e) => setVaultPath(e.target.value)}
                                    className="w-full bg-zinc-900 border border-zinc-700 p-2 text-white outline-none focus:border-amber-500 mb-2 font-mono text-[10px]"
                                    placeholder="e.g., C:/Users/Notes/SAGA_Lore"
                                />
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
                                <p className="text-[10px] text-zinc-500 mb-2">Provide a filename (e.g. map.png) in the saga_architect folder to bypass tectonics.</p>
                                <input
                                    type="text" placeholder="Leave blank for procedural" value={heightmap} onChange={(e) => setHeightmap(e.target.value)}
                                    className="w-full bg-zinc-900 border border-zinc-700 p-2 text-white outline-none focus:border-amber-500"
                                />
                            </div>
                        </div>
                    )}

                    {/* CLIMATE TAB */}
                    {activeTab === 'CLIMATE' && (
                        <div className="space-y-6">
                            <div>
                                <label className="text-blue-400 font-bold uppercase mb-2 block">Global Base Temperatures</label>
                                <div className="grid grid-cols-2 gap-2 mb-2">
                                    <span className="text-zinc-500">North Pole Min/Max</span>
                                    <input type="text" value={`${northPole[0]},${northPole[1]}`} onChange={(e) => setNorthPole(e.target.value.split(',').map(Number))} className="bg-zinc-950 border border-zinc-700 p-1 text-center text-white" />
                                    <span className="text-zinc-500">Equator Min/Max</span>
                                    <input type="text" value={`${equator[0]},${equator[1]}`} onChange={(e) => setEquator(e.target.value.split(',').map(Number))} className="bg-zinc-950 border border-zinc-700 p-1 text-center text-white" />
                                    <span className="text-zinc-500">South Pole Min/Max</span>
                                    <input type="text" value={`${southPole[0]},${southPole[1]}`} onChange={(e) => setSouthPole(e.target.value.split(',').map(Number))} className="bg-zinc-950 border border-zinc-700 p-1 text-center text-white" />
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
                                <div key={i} className="p-3 border border-zinc-800 bg-zinc-950">
                                    <span className="text-white font-bold">{lf.name}</span> <span className="text-zinc-500">({lf.type})</span>
                                    <div className="mt-2 text-[10px] text-zinc-400">
                                        Temp: {lf.min_temp}°C to {lf.max_temp}°C | Spawn: {lf.spawn_chance * 100}%
                                    </div>
                                </div>
                            ))}
                            <button onClick={() => setLifeforms([...lifeforms, { name: "New Creature", type: "FAUNA", is_aggressive: false, min_temp: 0, max_temp: 30, spawn_chance: 0.1, allowed_biomes: ["ANY"] }])} className="w-full border border-dashed border-green-800 text-green-500 py-2 hover:bg-green-900/20 transition-colors">+ Add Lifeform</button>
                        </div>
                    )}

                    {/* FACTIONS TAB */}
                    {activeTab === 'FACTIONS' && (
                        <div className="space-y-4">
                            <label className="text-red-500 font-bold uppercase mb-2 block">Custom Cultures</label>
                            {factions.map((f, i) => (
                                <div key={i} className="p-3 border border-zinc-800 bg-zinc-950">
                                    <span className="text-white font-bold">{f.name}</span>
                                    <div className="grid grid-cols-2 gap-1 mt-2 text-[10px] text-zinc-400">
                                        <span>Aggression: {f.aggression}</span>
                                        <span>Fighter: {f.will_fight ? 'Yes' : 'No'}</span>
                                        <span>Farmer: {f.will_farm ? 'Yes' : 'No'}</span>
                                        <span>Miner: {f.will_mine ? 'Yes' : 'No'}</span>
                                    </div>
                                    <div className="mt-2 text-[9px]">
                                        <span className="text-green-500">Loves: {f.loved_resources.join(', ')}</span><br />
                                        <span className="text-red-500">Hates: {f.hated_resources.join(', ')}</span>
                                    </div>
                                </div>
                            ))}
                            <button onClick={() => setFactions([...factions, { name: "New_Faction", aggression: 0.5, will_fight: true, will_farm: true, will_mine: false, loved_resources: ["Wood"], hated_resources: [] }])} className="w-full border border-dashed border-red-800 text-red-500 py-2 hover:bg-red-900/20 transition-colors">+ Add Faction</button>
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

                {/* Hex Inspector HUD */}
                {selectedHex && (
                    <div className="absolute top-6 right-6 w-72 bg-zinc-900/95 border border-amber-900/50 p-5 shadow-2xl backdrop-blur-md z-20">
                        <h4 className="text-sm font-bold text-amber-500 uppercase tracking-widest mb-3 border-b border-zinc-800 pb-2 flex justify-between">
                            <span>Hex #{selectedHex.id}</span>
                            <span className="text-zinc-500">[{Math.round(selectedHex.x)}, {Math.round(selectedHex.y)}]</span>
                        </h4>

                        <ul className="text-xs font-mono space-y-2">
                            <li className="flex justify-between"><span className="text-zinc-500">Biome</span><span className="text-white font-bold">{selectedHex.biome_tag}</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Elevation</span><span className="text-white">{(selectedHex.elevation * 100).toFixed(1)}%</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Temp</span><span className="text-red-400">{selectedHex.temperature.toFixed(1)}°C</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Moisture</span><span className="text-blue-400">{(selectedHex.moisture * 100).toFixed(0)}%</span></li>
                            <li className="flex justify-between"><span className="text-zinc-500">Wind</span><span className="text-zinc-300">[{selectedHex.wind_dx.toFixed(1)}, {selectedHex.wind_dy.toFixed(1)}]</span></li>
                        </ul>

                        <div className="mt-4 pt-3 border-t border-zinc-800 space-y-3">
                            {selectedHex.faction_owner ? (
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase block">Territory</span>
                                    <span className="text-xs font-bold text-red-400">{selectedHex.faction_owner}</span>
                                </div>
                            ) : <span className="text-[10px] text-zinc-600 uppercase italic">Unclaimed</span>}

                            {selectedHex.local_lifeforms?.length > 0 && (
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase block mb-1">Detected Lifeforms</span>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedHex.local_lifeforms.map((lf: string) => (
                                            <span key={lf} className="px-2 py-1 bg-zinc-950 border border-zinc-800 text-[10px] text-green-400">{lf}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
