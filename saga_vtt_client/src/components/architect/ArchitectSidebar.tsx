import React from 'react';
import {
    Globe, Cloud, Trees, Pickaxe, Users,
    Shield, Ghost, Landmark, Paintbrush,
    Calendar, Flame
} from 'lucide-react';
import type { TabType, ArchitectTab } from './types';

interface ArchitectSidebarProps {
    activeTab: TabType;
    onTabChange: (tab: TabType) => void;
}

export const ARCHITECT_TABS: ArchitectTab[] = [
    { id: 'GEOGRAPHY', label: 'Geography', icon: Globe, color: 'text-blue-400' },
    { id: 'CLIMATE', label: 'Climate', icon: Cloud, color: 'text-cyan-400' },
    { id: 'BIOMES', label: 'Biomes', icon: Flame, color: 'text-orange-400' },
    { id: 'RESOURCES', label: 'Resources', icon: Pickaxe, color: 'text-amber-400' },
    { id: 'ECOSYSTEM', label: 'Ecosystem', icon: Trees, color: 'text-emerald-400' },
    { id: 'CULTURES', label: 'Cultures', icon: Users, color: 'text-yellow-400' },
    { id: 'FACTIONS', label: 'Factions', icon: Shield, color: 'text-red-400' },
    { id: 'RELIGIONS', label: 'Religions', icon: Ghost, color: 'text-purple-400' },
    { id: 'BUILDINGS', label: 'Buildings', icon: Landmark, color: 'text-orange-600' },
    { id: 'PAINTING', label: 'Painting', icon: Paintbrush, color: 'text-pink-400' },
    { id: 'CHRONOS', label: 'Chronos', icon: Calendar, color: 'text-zinc-400' },
];

export const ArchitectSidebar: React.FC<ArchitectSidebarProps> = ({ activeTab, onTabChange }) => {
    return (
        <div className="w-20 lg:w-48 h-full bg-zinc-950/80 backdrop-blur-xl border-r border-white/5 flex flex-col py-6 z-50">
            <div className="px-4 mb-8 text-center lg:text-left">
                <h2 className="hidden lg:block text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-1">Module:</h2>
                <h1 className="text-sm font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white to-zinc-600 uppercase">God Engine</h1>
            </div>

            <nav className="flex-grow space-y-1 px-2 overflow-y-auto scrollbar-none">
                {ARCHITECT_TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;

                    return (
                        <button
                            key={tab.id}
                            onClick={() => onTabChange(tab.id)}
                            className={`
                                w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-300 group relative
                                ${isActive
                                    ? 'bg-white/5 text-white shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] border border-white/10'
                                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02] border border-transparent'
                                }
                            `}
                        >
                            {/* Active Glow Indicator */}
                            {isActive && (
                                <div className={`absolute left-0 w-1 h-4 rounded-full ${tab.color.replace('text-', 'bg-')} shadow-[0_0_10px_currentColor]`} />
                            )}

                            <Icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110 ${isActive ? tab.color : 'text-zinc-600'}`} />
                            <span className="hidden lg:block text-[11px] font-bold uppercase tracking-widest truncate">{tab.label}</span>

                            {/* Tooltip for small screens */}
                            <div className="lg:hidden absolute left-full ml-4 px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-[10px] font-bold opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap uppercase tracking-widest">
                                {tab.label}
                            </div>
                        </button>
                    );
                })}
            </nav>

            <div className="px-4 mt-auto pt-6 border-t border-white/5">
                <div className="hidden lg:block p-3 rounded-xl bg-gradient-to-br from-zinc-900 to-black border border-white/5 text-center">
                    <p className="text-[9px] text-zinc-500 font-bold uppercase leading-tight">System Status</p>
                    <p className="text-[10px] text-emerald-500 font-mono mt-1">NOMINAL (OK)</p>
                </div>
            </div>
        </div>
    );
};
