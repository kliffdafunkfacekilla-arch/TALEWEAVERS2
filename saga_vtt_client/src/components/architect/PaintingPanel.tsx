import { Paintbrush, Info, Hexagon, Mountain, Shield, Trees } from 'lucide-react';

interface PaintingPanelProps {
    editMode: string;
    setEditMode: (val: any) => void;
    activeBrush: string | number;
    setActiveBrush: (val: any) => void;
    brushSize: number;
    setBrushSize: (val: number) => void;
    brushStrength: number;
    setBrushStrength: (val: number) => void;
}

export const PaintingPanel: React.FC<PaintingPanelProps> = ({
    editMode, setEditMode,
    activeBrush, setActiveBrush,
    brushSize, setBrushSize,
    brushStrength, setBrushStrength
}) => {
    const MODES = [
        { id: 'NONE', label: 'Inspect', icon: Hexagon, color: 'text-zinc-500' },
        { id: 'ELEVATION', label: 'Elevation', icon: Mountain, color: 'text-blue-400' },
        { id: 'BIOME', label: 'Biomes', icon: Trees, color: 'text-emerald-400' },
        { id: 'FACTION', label: 'Factions', icon: Shield, color: 'text-red-400' },
    ];

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-pink-400 mb-2 flex items-center gap-2">
                    <Paintbrush className="w-4 h-4" /> 10. The Architect's Palette
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Perform manual adjustments and localized interventions on the global canvas.
                </p>
            </div>

            {/* Tool Selection */}
            <div className="grid grid-cols-2 gap-2">
                {MODES.map(mode => {
                    const Icon = mode.icon;
                    const isActive = editMode === mode.id;
                    return (
                        <button
                            key={mode.id}
                            onClick={() => { setEditMode(mode.id); setActiveBrush(mode.id === 'ELEVATION' ? 0.3 : ''); }}
                            className={`
                                flex items-center gap-2 p-3 rounded-2xl border transition-all duration-300
                                ${isActive
                                    ? 'bg-white/5 border-pink-500/50 text-white shadow-[0_5px_15px_rgba(236,72,153,0.1)]'
                                    : 'bg-zinc-950 border-white/5 text-zinc-500 hover:text-zinc-300 hover:border-white/10'
                                }
                            `}
                        >
                            <Icon className={`w-4 h-4 ${isActive ? mode.color : 'text-zinc-600'}`} />
                            <span className="text-[10px] font-black uppercase tracking-widest">{mode.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Brush Settings */}
            {editMode !== 'NONE' && (
                <div className="p-6 bg-zinc-900/40 border border-white/5 rounded-3xl space-y-6">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center text-[10px] font-black text-zinc-500 uppercase tracking-widest">
                            <span>Brush Radius</span>
                            <span className="text-white font-mono">{brushSize} Hexes</span>
                        </div>
                        <input
                            type="range" min="1" max="25" step="1"
                            value={brushSize} onChange={(e) => setBrushSize(Number(e.target.value))}
                            className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-pink-500"
                        />
                    </div>

                    <div className="space-y-4">
                        <div className="flex justify-between items-center text-[10px] font-black text-zinc-500 uppercase tracking-widest">
                            <span>Influence Density</span>
                            <span className="text-white font-mono">{brushStrength}%</span>
                        </div>
                        <input
                            type="range" min="10" max="100" step="10"
                            value={brushStrength} onChange={(e) => setBrushStrength(Number(e.target.value))}
                            className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-pink-500"
                        />
                    </div>
                </div>
            )}

            {/* Brush Data Selection */}
            {editMode === 'ELEVATION' && (
                <div className="grid grid-cols-3 gap-2 p-2 bg-black/40 border border-white/5 rounded-2xl">
                    <button onClick={() => setActiveBrush(0.1)} className={`py-2 text-[9px] font-black uppercase rounded-lg transition-all ${activeBrush === 0.1 ? 'bg-blue-900 text-blue-200 border border-blue-500' : 'text-zinc-600 hover:text-zinc-400'}`}>Trench</button>
                    <button onClick={() => setActiveBrush(0.3)} className={`py-2 text-[9px] font-black uppercase rounded-lg transition-all ${activeBrush === 0.3 ? 'bg-emerald-900 text-emerald-200 border border-emerald-500' : 'text-zinc-600 hover:text-zinc-400'}`}>Land</button>
                    <button onClick={() => setActiveBrush(0.9)} className={`py-2 text-[9px] font-black uppercase rounded-lg transition-all ${activeBrush === 0.9 ? 'bg-zinc-200 text-zinc-950 border border-zinc-300 shadow-lg' : 'text-zinc-600 hover:text-zinc-400'}`}>Peak</button>
                </div>
            )}

            {['BIOME', 'FACTION'].includes(editMode) && (
                <div className="space-y-3">
                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest block px-2">Layer Target</label>
                    <input
                        type="text"
                        value={activeBrush as string}
                        onChange={e => setActiveBrush(e.target.value)}
                        placeholder={`Enter ${editMode} name...`}
                        className="w-full bg-zinc-950 border border-white/5 p-4 rounded-2xl text-xs text-white focus:border-pink-500 outline-none placeholder:text-zinc-800 font-bold"
                    />
                    <div className="flex items-center gap-2 px-2">
                        <Info className="w-3 h-3 text-zinc-600" />
                        <p className="text-[9px] text-zinc-600 font-medium italic">Painting overrides procedural generation for these cells.</p>
                    </div>
                </div>
            )}
        </div>
    );
};
