import React from 'react';
import { useGameStore } from '../../store/useGameStore';

export const InventoryPanel: React.FC = () => {
    const inventory = useGameStore((s) => s.inventory_slots);

    // Mock mapping for icons if not provided by backend yet
    const iconMapping: Record<string, { sheet: string, x: number, y: number }> = {
        'Steel Rapier': { sheet: '/assets/icons/weapons1.png', x: 32, y: 0 },
        'Traveler\'s Bread': { sheet: '/assets/icons/Food.png', x: 0, y: 0 },
        'Mending Salve': { sheet: '/assets/icons/Food.png', x: 64, y: 32 },
    };

    return (
        <div className="space-y-4">
            <h3 className="text-[10px] font-bold uppercase tracking-[0.25em] text-amber-500/80 pl-1 border-b border-zinc-800 pb-2">
                ◆ Inventory Storage
            </h3>

            <div className="grid grid-cols-1 gap-2">
                {inventory.map((slot) => {
                    const icon = slot.itemName ? iconMapping[slot.itemName] : null;

                    return (
                        <div key={slot.id} className="bg-zinc-950 border border-zinc-900 p-2 flex items-center gap-3 group hover:border-zinc-700 transition-colors">
                            <div className="w-10 h-10 bg-zinc-900 border border-zinc-800 flex items-center justify-center overflow-hidden">
                                {icon ? (
                                    <div
                                        style={{
                                            width: '32px',
                                            height: '32px',
                                            backgroundImage: `url(${icon.sheet})`,
                                            backgroundPosition: `-${icon.x}px -${icon.y}px`,
                                            imageRendering: 'pixelated',
                                            transform: 'scale(1.2)'
                                        }}
                                    />
                                ) : (
                                    <div className="w-2 h-2 bg-zinc-800 rounded-full" />
                                )}
                            </div>

                            <div className="flex-grow">
                                <div className="text-[11px] font-bold text-zinc-300 uppercase truncate">
                                    {slot.itemName || 'Empty Slot'}
                                </div>
                                <div className="text-[9px] text-zinc-600 italic">
                                    {slot.itemName ? 'Item ready for use' : 'No item present'}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="p-2 bg-zinc-900/50 border border-zinc-800 text-[10px] text-zinc-500 italic">
                Items can be consumed or equipped from the Loadout Deck below.
            </div>
        </div>
    );
};
