import { useState } from 'react';
import { useGameStore } from '../store/useGameStore';
import { useCharacterStore } from '../store/useCharacterStore';

export function CampaignSetup({ onCommence }: { onCommence: (settings: any) => void }) {
    const characterName = useCharacterStore((s) => s.characterName);
    const setScreen = useGameStore((s) => s.setScreen);

    const [difficulty, setDifficulty] = useState('STANDARD');
    const [style, setStyle] = useState('GRITTY_SURVIVAL');
    const [length, setLength] = useState('SAGA');
    const [noFlyList, setNoFlyList] = useState('');
    const [partySize, setPartySize] = useState('SOLO');

    const handleStart = () => {
        const settings = {
            party_size: partySize,
            difficulty: difficulty,
            style: style,
            length: length,
            no_fly_list: noFlyList.split(',').map(s => s.trim()).filter(s => s.length > 0)
        };
        onCommence(settings);
    };

    return (
        <div className="w-screen h-screen bg-zinc-950 flex flex-col items-center justify-center text-white overflow-y-auto pt-12 pb-12">
            <h2 className="text-4xl font-bold tracking-widest mb-2 text-zinc-300 uppercase">
                Campaign Calibration
            </h2>
            <p className="text-zinc-500 text-sm mb-8 tracking-wider uppercase">System Parameters: Session Zero</p>

            <div className="w-[800px] border border-zinc-800 p-8 flex flex-col gap-8 bg-black/50 shadow-[0_0_50px_rgba(0,0,0,0.8)]">

                {/* Protocol 1: Party */}
                <div>
                    <h3 className="text-amber-500 font-bold uppercase mb-2 border-b border-zinc-800 pb-2">I. The Roster</h3>
                    <div className="flex gap-4 mt-4">
                        <button onClick={() => setPartySize('SOLO')} className={`flex-1 py-3 border text-sm font-bold tracking-widest uppercase transition-all ${partySize === 'SOLO' ? 'border-amber-500 bg-amber-900/20 text-amber-400' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>
                            Lone Wanderer
                            <div className="text-[10px] text-zinc-500 mt-1 normal-case font-normal tracking-normal">{characterName} only</div>
                        </button>
                        <button onClick={() => setPartySize('PARTY')} className={`flex-1 py-3 border text-sm font-bold tracking-widest uppercase transition-all opacity-50 cursor-not-allowed ${partySize === 'PARTY' ? 'border-amber-500 bg-amber-900/20 text-amber-400' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>
                            Full Party
                            <div className="text-[10px] text-zinc-500 mt-1 normal-case font-normal tracking-normal">Multiplayer Sync (Coming Soon)</div>
                        </button>
                    </div>
                </div>

                {/* Protocol 2: Difficulty */}
                <div>
                    <h3 className="text-red-500 font-bold uppercase mb-2 border-b border-zinc-800 pb-2">II. Threat Scaling</h3>
                    <div className="flex gap-4 mt-4">
                        <button onClick={() => setDifficulty('STORY')} className={`flex-1 py-3 border text-sm font-bold tracking-widest uppercase transition-all ${difficulty === 'STORY' ? 'border-red-500 bg-red-900/20 text-red-400' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>
                            Story
                            <div className="text-[10px] text-zinc-500 mt-1 normal-case font-normal tracking-normal">Lower tension, fewer hazards.</div>
                        </button>
                        <button onClick={() => setDifficulty('STANDARD')} className={`flex-1 py-3 border text-sm font-bold tracking-widest uppercase transition-all ${difficulty === 'STANDARD' ? 'border-red-500 bg-red-900/20 text-red-400' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>
                            Standard
                            <div className="text-[10px] text-zinc-500 mt-1 normal-case font-normal tracking-normal">Balanced T.A.L.E.W.E.A.V.E.R rules.</div>
                        </button>
                        <button onClick={() => setDifficulty('PUNISHING')} className={`flex-1 py-3 border text-sm font-bold tracking-widest uppercase transition-all ${difficulty === 'PUNISHING' ? 'border-red-500 bg-red-900/20 text-red-400' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>
                            Punishing
                            <div className="text-[10px] text-zinc-500 mt-1 normal-case font-normal tracking-normal">Rapid tension, lethal enemies.</div>
                        </button>
                    </div>
                </div>

                {/* Protocol 3: Narrative Tone & Length */}
                <div className="flex gap-8">
                    <div className="flex-1">
                        <h3 className="text-emerald-500 font-bold uppercase mb-2 border-b border-zinc-800 pb-2">III. Narrative Tone</h3>
                        <select
                            value={style}
                            onChange={(e) => setStyle(e.target.value)}
                            className="w-full mt-4 bg-zinc-900 border border-zinc-700 px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500 uppercase tracking-wider font-bold"
                        >
                            <option value="GRITTY_SURVIVAL">Gritty Survival</option>
                            <option value="HIGH_FANTASY">High Fantasy Epic</option>
                            <option value="DARK_HORROR">Dark Horror / Mystery</option>
                            <option value="POLITICAL_INTRIGUE">Political Intrigue</option>
                        </select>
                    </div>
                    <div className="flex-1">
                        <h3 className="text-emerald-500 font-bold uppercase mb-2 border-b border-zinc-800 pb-2">IV. Arc Length</h3>
                        <select
                            value={length}
                            onChange={(e) => setLength(e.target.value)}
                            className="w-full mt-4 bg-zinc-900 border border-zinc-700 px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500 uppercase tracking-wider font-bold"
                        >
                            <option value="ONE_SHOT">Short Arc (5 Milestones)</option>
                            <option value="SAGA">Standard Saga (15 Milestones)</option>
                            <option value="EPIC">Epic Campaign (Infinite)</option>
                        </select>
                    </div>
                </div>

                {/* Protocol 4: Safety Tools (No-Fly List) */}
                <div>
                    <h3 className="text-purple-500 font-bold uppercase mb-2 border-b border-zinc-800 pb-2">V. Safety Overrides (No-Fly List)</h3>
                    <p className="text-[11px] text-zinc-500 mb-2 mt-2">Specify themes, phobias, or topics the AI Director must NEVER reference or generate. Separate by commas.</p>
                    <textarea
                        value={noFlyList}
                        onChange={(e) => setNoFlyList(e.target.value)}
                        placeholder="e.g. spiders, excessive gore, clowns"
                        className="w-full h-24 bg-zinc-900 border border-zinc-700 p-4 text-sm text-white focus:outline-none focus:border-purple-500 placeholder-zinc-700 font-mono"
                    />
                </div>

                {/* Submit Block */}
                <div className="pt-4 flex gap-4">
                    <button
                        onClick={() => setScreen('MAIN_MENU')}
                        className="px-8 py-4 border border-zinc-700 text-zinc-400 hover:bg-zinc-800 uppercase tracking-widest text-sm font-bold transition-all"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleStart}
                        className="flex-1 px-8 py-4 border border-amber-600 bg-amber-900/20 text-amber-400 hover:bg-amber-900/40 uppercase tracking-widest text-sm font-bold shadow-[0_0_20px_rgba(217,119,6,0.15)] transition-all"
                    >
                        Commence Campaign
                    </button>
                </div>
            </div>
        </div>
    );
}
