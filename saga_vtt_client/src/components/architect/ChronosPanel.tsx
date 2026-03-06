import { Calendar, Sun, Moon } from 'lucide-react';

interface ChronosPanelProps {
    // We'll keep this simple for now as per the current state
    onBack: () => void;
}

export const ChronosPanel: React.FC<ChronosPanelProps> = () => {
    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-zinc-400 mb-2 flex items-center gap-2">
                    <Calendar className="w-4 h-4" /> 11. Temporal Mechanics
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Configure the orbital rotation and seasonal oscillations of the local sun.
                </p>
            </div>

            <div className="p-8 border border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-16 h-16 rounded-3xl bg-white/5 flex items-center justify-center border border-white/10 shadow-2xl">
                    <Moon className="w-8 h-8 text-zinc-700 animate-pulse" />
                </div>
                <div className="space-y-2">
                    <h4 className="text-xs font-black uppercase tracking-widest text-zinc-300">Stellar Sync Required</h4>
                    <p className="text-[10px] text-zinc-600 font-medium leading-relaxed max-w-[200px]">
                        The Chronos module requires a generated world to calibrate seasonal light curves.
                    </p>
                </div>
            </div>

            <div className="p-4 bg-zinc-900/40 border border-white/5 rounded-2xl flex items-center gap-4">
                <div className="p-2 bg-amber-500/10 rounded-xl">
                    <Sun className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                    <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block">Solar Cycle</span>
                    <span className="text-[11px] font-bold text-white">365 Days / 4 Seasons</span>
                </div>
            </div>

            <div className="p-4 bg-zinc-900/40 border border-white/5 rounded-2xl flex items-center gap-4 opacity-50">
                <div className="p-2 bg-blue-500/10 rounded-xl">
                    <Moon className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                    <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block">Lunar Phases</span>
                    <span className="text-[11px] font-bold text-white">LOCKED (Pending Export)</span>
                </div>
            </div>
        </div>
    );
};
