import React from 'react';
import { Plus, Trash2, Users, Briefcase, Zap } from 'lucide-react';

interface CulturePanelProps {
    cultures: any[];
    setCultures: (cultures: any[]) => void;
    factions: any[];
}

export const CulturePanel: React.FC<CulturePanelProps> = ({ cultures, setCultures, factions }) => {
    const addCulture = () => {
        setCultures([...cultures, {
            name: "New Group",
            resource_dependencies: ["Food", "Water"],
            common_role: "Farmer",
            faction_affiliations: []
        }]);
    };

    const updateCulture = (idx: number, field: string, value: any) => {
        const newCultures = [...cultures];
        newCultures[idx] = { ...newCultures[idx], [field]: value };
        setCultures(newCultures);
    };

    const removeCulture = (idx: number) => {
        setCultures(cultures.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em] text-yellow-500 mb-2 flex items-center gap-2">
                    <Users className="w-4 h-4" /> 07. Demographics & Society
                </h3>
                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed uppercase">
                    Define the diverse inhabitants of your world, their daily needs, and their social alignments.
                </p>
            </div>

            <div className="flex-grow flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Social Groups</h3>
                    <button onClick={addCulture} className="flex items-center gap-1.5 px-3 py-1 bg-yellow-500/10 border border-yellow-500/20 rounded-full text-[9px] font-black uppercase text-yellow-500 hover:bg-yellow-500/20 transition-colors">
                        <Plus className="w-3 h-3" /> New Culture
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    {cultures.map((c, i) => (
                        <div key={i} className="group p-4 bg-zinc-900/40 border border-white/5 rounded-2xl hover:border-yellow-500/30 transition-all duration-300">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-8 h-8 rounded-xl bg-yellow-500/10 flex items-center justify-center border border-yellow-500/20">
                                    <Users className="w-4 h-4 text-yellow-500" />
                                </div>
                                <input
                                    type="text"
                                    value={c.name}
                                    onChange={e => updateCulture(i, 'name', e.target.value)}
                                    className="flex-grow bg-transparent text-xs font-black uppercase tracking-widest text-white border-none outline-none focus:text-yellow-500 transition-colors"
                                    placeholder="CULTURE_NAME"
                                />
                                <button onClick={() => removeCulture(i)} className="text-zinc-600 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                    <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2"><Briefcase className="w-3 h-3" /> Default Role</span>
                                    <select
                                        value={c.common_role}
                                        onChange={e => updateCulture(i, 'common_role', e.target.value)}
                                        className="w-full bg-transparent text-[10px] font-bold text-zinc-300 outline-none"
                                    >
                                        {["Farmer", "Admin", "Services", "Soldier", "Scholar", "Laborer", "Artisan", "Merchant", "Criminal", "Clergy"].map(role => (
                                            <option key={role} value={role}>{role}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="p-3 bg-black/40 border border-white/5 rounded-xl space-y-2">
                                    <span className="text-[8px] font-black text-zinc-600 uppercase flex items-center gap-2"><Zap className="w-3 h-3" /> Dependencies</span>
                                    <input
                                        type="text"
                                        value={c.resource_dependencies?.join(', ')}
                                        onChange={e => updateCulture(i, 'resource_dependencies', e.target.value.split(',').map(s => s.trim()))}
                                        className="w-full bg-transparent text-[10px] text-zinc-300 outline-none border-b border-white/5 focus:border-yellow-500"
                                        placeholder="Food, Iron..."
                                    />
                                </div>
                            </div>

                            {/* Faction Affiliations */}
                            <div className="space-y-2">
                                <span className="text-[9px] font-black text-zinc-500 uppercase flex items-center justify-between">
                                    Faction Affiliation
                                    <button
                                        onClick={() => updateCulture(i, 'faction_affiliations', [...(c.faction_affiliations || []), { faction: "", population_pct: 0.1 }])}
                                        className="text-yellow-500 hover:text-yellow-400 font-bold"
                                    >
                                        + Join
                                    </button>
                                </span>
                                <div className="space-y-2">
                                    {c.faction_affiliations?.map((aff: any, ai: number) => (
                                        <div key={ai} className="flex items-center gap-2 bg-zinc-950/50 p-2 rounded-lg border border-white/5">
                                            <select
                                                value={aff.faction}
                                                onChange={e => {
                                                    const newAffs = [...c.faction_affiliations];
                                                    newAffs[ai].faction = e.target.value;
                                                    updateCulture(i, 'faction_affiliations', newAffs);
                                                }}
                                                className="flex-grow bg-transparent text-[10px] text-zinc-400 outline-none"
                                            >
                                                <option value="">Unallied</option>
                                                {factions.map(f => <option key={f.name} value={f.name}>{f.name}</option>)}
                                            </select>
                                            <input
                                                type="number" min="0" max="1" step="0.1"
                                                value={aff.population_pct}
                                                onChange={e => {
                                                    const newAffs = [...c.faction_affiliations];
                                                    newAffs[ai].population_pct = Number(e.target.value);
                                                    updateCulture(i, 'faction_affiliations', newAffs);
                                                }}
                                                className="w-10 bg-zinc-900 border border-white/5 text-[10px] text-white text-center rounded"
                                            />
                                            <button onClick={() => {
                                                updateCulture(i, 'faction_affiliations', c.faction_affiliations.filter((_: any, idx: number) => idx !== ai));
                                            }} className="text-zinc-700 hover:text-red-500 px-1 font-bold">×</button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
