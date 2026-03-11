import React, { useEffect, useState } from 'react';

export const CalendarEditor: React.FC = () => {
    const [calendar, setCalendar] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'months' | 'seasons'>('months');

    useEffect(() => {
        const architectUrl = import.meta.env.VITE_SAGA_ARCHITECT_URL || 'http://localhost:8013';
        fetch(`${architectUrl}/api/config/calendar`)
            .then(res => res.json())
            .then(data => setCalendar(data))
            .catch(() => console.error("Failed to load Calendar config. Is Port 9000 running?"));
    }, []);

    const saveConfig = () => {
        const architectUrl = import.meta.env.VITE_SAGA_ARCHITECT_URL || 'http://localhost:8013';
        fetch(`${architectUrl}/api/config/calendar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(calendar)
        }).then(() => alert("God Engine Calendar Updated!"))
            .catch(() => alert("Save failed. Is Port 9000 running?"));
    };

    const resetToStandard = () => {
        const monthNames = [
            "Dawnspire", "Floralis", "Greenbloom",
            "Goldensun", "Highfever", "Sunsear",
            "Harvestride", "Embershake", "Leafsfall",
            "Frostveil", "Deepbite", "Ironwind"
        ];

        const newMonths = monthNames.map((name, i) => {
            let season = "Spring";
            if (i >= 3 && i < 6) season = "Summer";
            else if (i >= 6 && i < 9) season = "Autumn";
            else if (i >= 9) season = "Winter";

            return { name, days: 30, season };
        });

        const newCalendar = {
            months: newMonths,
            seasons: {
                "Spring": { temp_band: "MID", precipitation_chance: 0.4, weather_type: "Rain" },
                "Summer": { temp_band: "HIGH", precipitation_chance: 0.2, weather_type: "Rain" },
                "Autumn": { temp_band: "MID", precipitation_chance: 0.6, weather_type: "Rain" },
                "Winter": { temp_band: "LOW", precipitation_chance: 0.3, weather_type: "Snow" }
            }
        };

        setCalendar(newCalendar);
    };

    if (!calendar) return <div className="text-zinc-500 p-4 border-t border-zinc-800 bg-zinc-950 text-xs font-mono uppercase tracking-widest">Loading Chronos Config... (Port 8004)</div>;

    return (
        <div className="w-full h-full bg-zinc-900 border-t border-zinc-800 text-zinc-300 flex flex-col font-mono text-xs mt-2 relative">
            <div className="flex justify-between items-center p-3 bg-black border-b border-zinc-700">
                <div className="flex flex-col">
                    <span className="font-bold text-blue-400 uppercase tracking-widest text-[10px]">Chronos Engine</span>
                    <button onClick={resetToStandard} className="text-[8px] text-zinc-500 hover:text-amber-500 uppercase font-bold text-left mt-0.5">↺ Reset to Standard</button>
                </div>
                <button onClick={saveConfig} className="bg-blue-900 hover:bg-blue-700 text-white px-3 py-1 text-[10px] uppercase font-bold tracking-wider transition-colors">SAVE L.O.D. RULES</button>
            </div>

            {/* TABS */}
            <div className="flex border-b border-zinc-700 bg-zinc-950">
                <button onClick={() => setActiveTab('months')} className={`flex-1 py-2 font-bold uppercase ${activeTab === 'months' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:bg-zinc-800/50'}`}>Cycle</button>
                <button onClick={() => setActiveTab('seasons')} className={`flex-1 py-2 font-bold uppercase ${activeTab === 'seasons' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:bg-zinc-800/50'}`}>Climate</button>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-4 max-h-[400px]">

                {/* MONTHS TAB */}
                {activeTab === 'months' && (
                    <>
                        {calendar.months.map((month: any, idx: number) => (
                            <div key={idx} className="flex flex-col gap-2 bg-black p-2 border border-zinc-800">
                                <div className="flex justify-between items-center border-b border-zinc-800 pb-1 mb-1">
                                    <span className="text-[10px] text-zinc-500 uppercase font-bold">Month {idx + 1}</span>
                                    <button onClick={() => { const newCal = { ...calendar }; newCal.months.splice(idx, 1); setCalendar(newCal); }} className="text-red-500 hover:text-red-400 text-[10px] uppercase">Remove</button>
                                </div>
                                <div className="flex gap-2">
                                    <div className="flex-1">
                                        <input type="text" value={month.name}
                                            onChange={(e) => { const newCal = { ...calendar }; newCal.months[idx].name = e.target.value; setCalendar(newCal); }}
                                            className="w-full bg-zinc-900 text-amber-500 font-bold border border-zinc-700 p-1" placeholder="Name" />
                                    </div>
                                    <div className="w-16">
                                        <input type="number" min="1" value={month.days}
                                            onChange={(e) => { const newCal = { ...calendar }; newCal.months[idx].days = parseInt(e.target.value); setCalendar(newCal); }}
                                            className="w-full bg-zinc-900 text-white font-mono text-center border border-zinc-700 p-1" />
                                    </div>
                                    <div className="flex-1">
                                        <input type="text" value={month.season}
                                            onChange={(e) => { const newCal = { ...calendar }; newCal.months[idx].season = e.target.value; setCalendar(newCal); }}
                                            className="w-full bg-zinc-900 text-white border border-zinc-700 p-1" placeholder="Season" />
                                    </div>
                                </div>
                            </div>
                        ))}
                        <button onClick={() => { const newCal = { ...calendar }; newCal.months.push({ name: "New_Month", days: 30, season: "Spring" }); setCalendar(newCal); }}
                            className="w-full py-2 border border-dashed border-zinc-700 text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors uppercase font-bold text-[10px]">
                            + ADD Custom Month
                        </button>
                    </>
                )}

                {/* SEASONS TAB */}
                {activeTab === 'seasons' && calendar.seasons && (
                    <div className="space-y-3">
                        {Object.keys(calendar.seasons).map((seasonKey) => {
                            const season = calendar.seasons[seasonKey];
                            return (
                                <div key={seasonKey} className="bg-black p-2 border border-zinc-800 flex flex-col gap-2">
                                    <div className="flex justify-between items-center border-b border-zinc-800 pb-1">
                                        <h4 className="text-yellow-500 font-bold uppercase">{seasonKey} RULES</h4>
                                        <button onClick={() => { const newCal = { ...calendar }; delete newCal.seasons[seasonKey]; setCalendar(newCal); }} className="text-red-500 hover:text-red-400 text-[10px] uppercase">Del</button>
                                    </div>

                                    <div className="flex justify-between items-center">
                                        <label className="text-[9px] text-zinc-500 uppercase w-2/3">Temp Band (Hex Math)</label>
                                        <select value={season.temp_band}
                                            onChange={(e) => { const newCal = { ...calendar }; newCal.seasons[seasonKey].temp_band = e.target.value; setCalendar(newCal); }}
                                            className="w-1/3 bg-zinc-900 text-blue-400 font-bold border border-zinc-700 p-1 text-center">
                                            <option value="LOW">LOW</option>
                                            <option value="MID">MID</option>
                                            <option value="HIGH">HIGH</option>
                                        </select>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <label className="text-[9px] text-zinc-500 uppercase w-1/2">Precipitation %</label>
                                        <input type="range" step="0.05" min="0" max="1" value={season.precipitation_chance}
                                            onChange={(e) => { const newCal = { ...calendar }; newCal.seasons[seasonKey].precipitation_chance = parseFloat(e.target.value); setCalendar(newCal); }}
                                            className="w-1/3 accent-blue-500" />
                                        <span className="w-[15%] text-right font-mono text-[10px]">{(season.precipitation_chance * 100).toFixed(0)}%</span>
                                    </div>

                                    <div className="flex justify-between items-center">
                                        <label className="text-[9px] text-zinc-500 uppercase w-2/3">Weather Class</label>
                                        <select value={season.weather_type}
                                            onChange={(e) => { const newCal = { ...calendar }; newCal.seasons[seasonKey].weather_type = e.target.value; setCalendar(newCal); }}
                                            className="w-1/3 bg-zinc-900 text-white border border-zinc-700 p-1 text-center">
                                            <option value="Rain">Rain</option>
                                            <option value="Snow">Snow</option>
                                            <option value="Drought">Drought</option>
                                        </select>
                                    </div>
                                </div>
                            );
                        })}
                        <button onClick={() => {
                            const newCal = { ...calendar };
                            const newName = prompt("Enter Season Name (e.g. Autumn):", "Autumn");
                            if (newName && !newCal.seasons[newName]) {
                                newCal.seasons[newName] = { temp_band: "MID", precipitation_chance: 0.5, weather_type: "Rain" };
                                setCalendar(newCal);
                            }
                        }}
                            className="w-full py-2 border border-dashed border-zinc-700 text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors uppercase font-bold text-[10px]">
                            + ADD CLIMATE RULE
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
