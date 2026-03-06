import React from 'react';
import { Thermometer, Wind, Droplets } from 'lucide-react';

interface ClimatePanelProps {
    northPole: [number, number];
    setNorthPole: (val: [number, number]) => void;
    equator: [number, number];
    setEquator: (val: [number, number]) => void;
    southPole: [number, number];
    setSouthPole: (val: [number, number]) => void;
    windBands: string[];
    updateWindBand: (idx: number, val: string) => void;
    rainMultiplier: number;
    setRainMultiplier: (val: number) => void;
}

export const ClimatePanel: React.FC<ClimatePanelProps> = ({
    northPole, setNorthPole,
    equator, setEquator,
    southPole, setSouthPole,
    windBands, updateWindBand,
    rainMultiplier, setRainMultiplier
}) => {
    const renderTempControl = (label: string, value: [number, number], setter: (val: [number, number]) => void, color: string) => (
        <div className="p-4 bg-zinc-900/40 border border-white/5 rounded-2xl space-y-3">
            <div className="flex justify-between items-center text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                <span>{label}</span>
                <span className="font-mono text-white bg-white/5 px-2 py-0.5 rounded border border-white/10">
                    {value[0]}°C to {value[1]}°C
                </span>
            </div>
            <div className="flex gap-4">
                <input
                    type="range" min="-100" max="100" value={value[0]}
                    onChange={(e) => setter([Number(e.target.value), value[1]])}
                    className={`w-1/2 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-${color}-500`}
                />
                <input
                    type="range" min="-100" max="100" value={value[1]}
                    onChange={(e) => setter([value[0], Number(e.target.value)])}
                    className={`w-1/2 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-${color}-500`}
                />
            </div>
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-cyan-400 mb-2 flex items-center gap-2">
                    <Thermometer className="w-4 h-4" /> 02. Thermal Gradients
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Configure the global thermodynamic engine and atmospheric flows.
                </p>
            </div>

            {/* Temperature Sections */}
            <div className="space-y-3">
                {renderTempControl("North Pole Base", northPole, setNorthPole, "blue")}
                {renderTempControl("Equatorial Belt", equator, setEquator, "orange")}
                {renderTempControl("South Pole Base", southPole, setSouthPole, "blue")}
            </div>

            {/* Wind Bands */}
            <div>
                <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-4 flex items-center gap-2">
                    <Wind className="w-3.5 h-3.5" /> Atmospheric Wind Latitudes
                </h3>
                <div className="grid grid-cols-7 gap-2">
                    {windBands.map((dir, i) => (
                        <div key={i} className="flex flex-col items-center gap-2">
                            <span className="text-[8px] font-black font-mono text-zinc-600">L{i + 1}</span>
                            <select
                                value={dir}
                                onChange={(e) => updateWindBand(i, e.target.value)}
                                className="w-full bg-zinc-900 border border-white/5 text-[10px] py-3 rounded-lg text-center text-white outline-none appearance-none hover:border-cyan-500/30 transition-colors font-bold"
                            >
                                {["N", "NE", "E", "SE", "S", "SW", "W", "NW"].map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                        </div>
                    ))}
                </div>
                <p className="text-[9px] text-zinc-600 mt-4 italic font-medium">Bands represent prevailing currents across 7 latitudinal tiers.</p>
            </div>

            {/* Rainfall */}
            <div className="p-4 bg-zinc-900/60 border border-white/5 rounded-2xl space-y-4">
                <div className="flex justify-between items-center text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    <span className="flex items-center gap-2"><Droplets className="w-3.5 h-3.5 text-blue-400" /> Global Precipitation</span>
                    <span className="font-mono text-white bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">x{rainMultiplier}</span>
                </div>
                <input
                    type="range" min="0" max="3" step="0.1" value={rainMultiplier}
                    onChange={(e) => setRainMultiplier(Number(e.target.value))}
                    className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
            </div>
        </div>
    );
};
