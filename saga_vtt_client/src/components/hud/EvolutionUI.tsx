import { useCharacterStore } from '../../store/useCharacterStore';
import { Star, Skull, HeartPulse, X } from 'lucide-react';

interface EvolutionUIProps {
    onClose: () => void;
}

export function EvolutionUI({ onClose }: EvolutionUIProps) {
    const { pip_bank, attributes, characterSheet, evolveAttribute, evolveSkill } = useCharacterStore();

    if (!characterSheet) return null;

    const PHYSICAL_STATS = ['might', 'endurance', 'vitality', 'fortitude', 'reflexes', 'finesse'];
    const MENTAL_STATS = ['knowledge', 'logic', 'charm', 'willpower', 'awareness', 'intuition'];
    const skills = Object.keys(characterSheet.tactical_skills || {});

    return (
        <div className="absolute inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-8">
            <div className="max-w-4xl w-full bg-zinc-950 border border-zinc-800 rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-full">
                {/* Header */}
                <div className="p-6 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
                    <div>
                        <h2 className="text-2xl font-bold tracking-tighter text-white uppercase italic">Biological Evolution</h2>
                        <p className="text-zinc-500 text-xs uppercase tracking-widest mt-1">Spend gained pips to restructure your form</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-zinc-800 rounded-full transition-colors">
                        <X className="w-6 h-6 text-zinc-500" />
                    </button>
                </div>

                {/* Pip Bar */}
                <div className="grid grid-cols-3 gap-4 p-6 bg-zinc-900/30 border-b border-zinc-800">
                    <div className="flex items-center gap-4 bg-amber-900/10 border border-amber-900/30 p-4 rounded-lg">
                        <div className="bg-amber-500/20 p-2 rounded-lg">
                            <Star className="w-6 h-6 text-amber-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-amber-500 uppercase">Star Pips</p>
                            <p className="text-2xl font-bold text-white tabular-nums">{pip_bank.stars}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 bg-red-900/10 border border-red-900/30 p-4 rounded-lg">
                        <div className="bg-red-500/20 p-2 rounded-lg">
                            <Skull className="w-6 h-6 text-red-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-red-500 uppercase">Scar Pips</p>
                            <p className="text-2xl font-bold text-white tabular-nums">{pip_bank.scars}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 bg-emerald-900/10 border border-emerald-900/30 p-4 rounded-lg">
                        <div className="bg-emerald-500/20 p-2 rounded-lg">
                            <HeartPulse className="w-6 h-6 text-emerald-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-emerald-500 uppercase">Survivor Pips</p>
                            <p className="text-2xl font-bold text-white tabular-nums">{pip_bank.survivors}</p>
                        </div>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-grow overflow-y-auto grid grid-cols-2 gap-8 p-8">
                    {/* Attributes (Stars) */}
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-xs font-black text-amber-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                                <Star className="w-3 h-3" /> Attribute Mutation [1 Star]
                            </h3>
                            <div className="grid grid-cols-1 gap-2">
                                {[...PHYSICAL_STATS, ...MENTAL_STATS].map(stat => (
                                    <button
                                        key={stat}
                                        onClick={() => evolveAttribute(stat)}
                                        disabled={pip_bank.stars <= 0}
                                        className="flex items-center justify-between p-3 bg-zinc-900/50 border border-zinc-800 rounded hover:border-amber-500/50 hover:bg-zinc-800 transition-all disabled:opacity-30 disabled:hover:border-zinc-800 disabled:hover:bg-zinc-900/50"
                                    >
                                        <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">{stat}</span>
                                        <span className="text-lg font-bold text-white">{attributes[stat]}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Skills (Scars) */}
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-xs font-black text-red-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                                <Skull className="w-3 h-3" /> Skill Mastery [1 Scar]
                            </h3>
                            <div className="grid grid-cols-1 gap-2">
                                {skills.map(skill => (
                                    <button
                                        key={skill}
                                        onClick={() => evolveSkill(skill)}
                                        disabled={pip_bank.scars <= 0}
                                        className="flex items-center justify-between p-3 bg-zinc-900/50 border border-zinc-800 rounded hover:border-red-500/50 hover:bg-zinc-800 transition-all disabled:opacity-30 disabled:hover:border-zinc-800 disabled:hover:bg-zinc-900/50"
                                    >
                                        <div className="text-left">
                                            <p className="text-xs font-bold uppercase tracking-wider text-zinc-300">{skill}</p>
                                            <p className="text-[10px] text-zinc-500 uppercase tracking-widest">
                                                Rank {characterSheet.tactical_skills![skill].rank} · Pips {characterSheet.tactical_skills![skill].pips}/5
                                            </p>
                                        </div>
                                        <div className="bg-red-500/10 px-2 py-1 rounded border border-red-500/20">
                                            <span className="text-xs font-black text-red-400">+1</span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Survivors */}
                        <div>
                            <h3 className="text-xs font-black text-emerald-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                                <HeartPulse className="w-3 h-3" /> Survival Instinct [1 Survivor]
                            </h3>
                            <button
                                disabled={pip_bank.survivors <= 0}
                                className="w-full flex items-center justify-center gap-3 p-6 bg-emerald-900/10 border border-emerald-900/30 rounded-lg hover:bg-emerald-900/20 transition-all disabled:opacity-30"
                            >
                                <HeartPulse className="w-5 h-5 text-emerald-500" />
                                <span className="text-sm font-black uppercase tracking-widest text-emerald-400 text-center">
                                    Restore All Survival Pools
                                </span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 bg-zinc-900/80 border-t border-zinc-800 text-center">
                    <p className="text-[10px] text-zinc-600 uppercase tracking-[0.3em]">Genetic Restructuring Terminal · S.A.G.A. Protocol</p>
                </div>
            </div>
        </div>
    );
}
