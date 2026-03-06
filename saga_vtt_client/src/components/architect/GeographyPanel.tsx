import React from 'react';
import { Plus, Trash2, Mountain, ChevronDown, LandPlot, Zap } from 'lucide-react';

interface GeographyPanelProps {
    hexCount: number;
    setHexCount: (val: number) => void;
    plateCount: number;
    setPlateCount: (val: number) => void;
    heightmapSteps: any[];
    setHeightmapSteps: (steps: any[]) => void;
    onGenerate: () => void;
    isGenerating: boolean;
}

export const GeographyPanel: React.FC<GeographyPanelProps> = ({
    hexCount, setHexCount,
    plateCount, setPlateCount,
    heightmapSteps, setHeightmapSteps,
    onGenerate, isGenerating
}) => {
    const addStep = () => {
        setHeightmapSteps([...heightmapSteps, { tool: "Hill", count: 10, height: 0.2, range_x: [0, 1], range_y: [0, 1] }]);
    };

    const updateStep = (idx: number, field: string, value: any) => {
        const newSteps = [...heightmapSteps];
        newSteps[idx] = { ...newSteps[idx], [field]: value };
        setHeightmapSteps(newSteps);
    };

    const removeStep = (idx: number) => {
        setHeightmapSteps(heightmapSteps.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-blue-400 mb-2 flex items-center gap-2">
                    <LandPlot className="w-4 h-4" /> 01. Crust & Tectonics
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the fundamental resolution and subterranean stress of your world.
                </p>
            </div>

            {/* Core Params */}
            <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-zinc-900/40 border border-white/5 rounded-2xl space-y-4">
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Hex Resolution</span>
                        <span className="text-xs font-mono text-white bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">{hexCount}</span>
                    </div>
                    <input
                        type="range" min="1000" max="100000" step="1000"
                        value={hexCount} onChange={(e) => setHexCount(Number(e.target.value))}
                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                </div>

                <div className="p-4 bg-zinc-900/40 border border-white/5 rounded-2xl space-y-4">
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Tectonic Plates</span>
                        <span className="text-xs font-mono text-white bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">{plateCount}</span>
                    </div>
                    <input
                        type="range" min="1" max="100" step="1"
                        value={plateCount} onChange={(e) => setPlateCount(Number(e.target.value))}
                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                </div>
            </div>

            {/* Sculpting Brushes */}
            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Procedural Sculpting Brushes</h3>
                    <button
                        onClick={addStep}
                        className="flex items-center gap-1.5 px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[9px] font-black uppercase text-zinc-300 hover:bg-white/10 transition-colors"
                    >
                        <Plus className="w-3 h-3" /> Add Brush
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {heightmapSteps.length === 0 && (
                        <div className="h-40 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-3xl text-zinc-700">
                            <Mountain className="w-8 h-8 mb-2 opacity-20" />
                            <p className="text-[10px] font-bold uppercase tracking-widest">No Active Brushes</p>
                        </div>
                    )}

                    {heightmapSteps.map((step, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/60 border border-white/5 rounded-2xl hover:border-blue-500/30 transition-all duration-300">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                                        <ChevronDown className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <div>
                                        <select
                                            value={step.tool}
                                            onChange={(e) => updateStep(i, 'tool', e.target.value)}
                                            className="bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none cursor-pointer"
                                        >
                                            <option value="Hill">Hill (Soft Rise)</option>
                                            <option value="Pit">Pit (Craters)</option>
                                            <option value="Range">Range (Ridges)</option>
                                            <option value="Smooth">Smooth (Erosion)</option>
                                        </select>
                                    </div>
                                </div>
                                <button onClick={() => removeStep(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                        <span>Brush Density</span>
                                        <span className="text-white font-mono">{step.count} Pts</span>
                                    </div>
                                    <input type="range" min="1" max="500" value={step.count} onChange={e => updateStep(i, 'count', Number(e.target.value))} className="w-full h-1 bg-zinc-800 accent-blue-500" />
                                </div>

                                {step.tool !== 'Smooth' && (
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">
                                            <span>Magnitude / Elevation</span>
                                            <span className="text-white font-mono">{step.height.toFixed(2)}m</span>
                                        </div>
                                        <input type="range" min="0.01" max="1.0" step="0.01" value={step.height} onChange={e => updateStep(i, 'height', Number(e.target.value))} className="w-full h-1 bg-zinc-800 accent-blue-500" />
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Global Actions */}
            <div className="pt-6 border-t border-white/5">
                <button
                    onClick={onGenerate}
                    disabled={isGenerating}
                    className={`
                        w-full py-5 rounded-3xl flex items-center justify-center gap-3 transition-all duration-500 group relative overflow-hidden
                        ${isGenerating
                            ? 'bg-zinc-800 border-zinc-700 cursor-not-allowed text-zinc-500'
                            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_10px_40px_rgba(37,99,235,0.3)] hover:shadow-[0_20px_50px_rgba(37,99,235,0.5)] border border-blue-400/30'
                        }
                    `}
                >
                    {isGenerating && <div className="absolute inset-0 bg-blue-400/10 animate-pulse" />}
                    <Zap className={`w-5 h-5 ${isGenerating ? 'animate-spin' : 'group-hover:scale-125 transition-transform'}`} />
                    <span className="text-sm font-black uppercase tracking-[0.2em]">
                        {isGenerating ? 'Architectural Convergence...' : 'Commence Generation'}
                    </span>
                </button>
            </div>
        </div>
    );
};
