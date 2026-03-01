import React, { useState, useEffect } from 'react';
import { useGameStore, type SurvivalJob } from '../../store/useGameStore';
import { useWorldStore } from '../../store/useWorldStore';
import { useCharacterStore } from '../../store/useCharacterStore';

export const SurvivalScreen: React.FC = () => {
    const selectedHex = useWorldStore((s) => s.selectedHex);
    const characterName = useCharacterStore((s) => s.characterName);
    const setVttTier = useGameStore((s) => s.setVttTier);
    const survivalJobs = useGameStore((s) => s.survivalJobs);
    const assignSurvivalJob = useGameStore((s) => s.assignSurvivalJob);
    const rations = useGameStore((s) => s.rations);
    const fuel = useGameStore((s) => s.fuel);

    // Dynamic background based on biome
    const [bgImage, setBgImage] = useState('/assets/parallax/forest_bg.png');

    useEffect(() => {
        if (!selectedHex) return;
        if (selectedHex.elevation > 0.8 || selectedHex.biome_tag === 'DEEP_TUNDRA') {
            setBgImage('/assets/parallax/mountain_bg.png');
        } else {
            setBgImage('/assets/parallax/forest_bg.png');
        }
    }, [selectedHex]);

    const jobs: SurvivalJob['jobName'][] = ['FORAGE', 'GUARD', 'FIRE', 'REST', 'REPAIR'];

    return (
        <div className="relative w-full h-full bg-black overflow-hidden flex flex-col items-center justify-center">
            {/* Parallax Background */}
            <div
                className="absolute inset-0 bg-cover bg-center transition-all duration-1000 ease-in-out scale-105"
                style={{ backgroundImage: `url(${bgImage})` }}
            />
            {/* Vignette Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/50 pointer-events-none" />

            {/* --- TOP HUD: Resources --- */}
            <div className="absolute top-8 left-1/2 -translate-x-1/2 flex gap-12 z-10">
                <div className="flex flex-col items-center">
                    <span className="text-[10px] text-zinc-500 uppercase tracking-[0.2em] mb-1">Supplies</span>
                    <div className="text-3xl font-bold text-amber-500 tracking-tighter">
                        {rations} <span className="text-sm font-light text-zinc-400">Rations</span>
                    </div>
                </div>
                <div className="flex flex-col items-center">
                    <span className="text-[10px] text-zinc-500 uppercase tracking-[0.2em] mb-1">Heat Source</span>
                    <div className="text-3xl font-bold text-orange-600 tracking-tighter">
                        {fuel} <span className="text-sm font-light text-zinc-400">Fuel</span>
                    </div>
                </div>
            </div>

            {/* --- CENTRAL UI: Job Board --- */}
            <div className="z-10 bg-zinc-950/80 backdrop-blur-md border border-zinc-800 p-8 rounded-xl shadow-2xl w-[500px]">
                <h2 className="text-xl font-bold tracking-widest text-white mb-2 uppercase border-b border-zinc-800 pb-2">
                    Nightfall Protocol
                </h2>
                <p className="text-xs text-zinc-400 mb-6 italic">
                    The sun dips below the horizon in the {selectedHex?.biome_tag.replace('_', ' ')}. Assign duties to survive the night.
                </p>

                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="text-sm font-bold text-white">{characterName}</span>
                            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Party Leader</span>
                        </div>
                        <div className="flex gap-2">
                            {jobs.map((job) => {
                                const isActive = survivalJobs.find(j => j.characterName === characterName && j.jobName === job);
                                return (
                                    <button
                                        key={job}
                                        onClick={() => assignSurvivalJob(characterName, job)}
                                        className={`px-3 py-1.5 rounded border text-[10px] font-bold transition-all ${isActive
                                            ? 'bg-amber-500 border-amber-400 text-black shadow-[0_0_10px_rgba(245,158,11,0.5)]'
                                            : 'bg-zinc-900 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-white'
                                            }`}
                                    >
                                        {job}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </div>

                <div className="mt-8 flex gap-4">
                    <button
                        onClick={() => setVttTier(2)}
                        className="flex-grow py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold uppercase tracking-widest rounded transition-all"
                    >
                        Abandon Camp
                    </button>
                    <button
                        className="flex-grow py-3 bg-red-900/40 hover:bg-red-900/60 text-red-100 text-xs font-bold uppercase tracking-widest rounded border border-red-700 transition-all"
                    >
                        Commence Phase
                    </button>
                </div>
            </div>

            {/* --- BOTTOM HUD: Atmosphere --- */}
            <div className="absolute bottom-12 text-center pointer-events-none">
                <div className="text-xs text-zinc-300 font-light tracking-[0.3em] uppercase opacity-60">
                    Tier 3: Survival Sequence Alpha
                </div>
            </div>
        </div>
    );
};
