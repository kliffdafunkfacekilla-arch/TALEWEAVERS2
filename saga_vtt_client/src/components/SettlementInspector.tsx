import React from 'react';
import { useWorldStore } from '../store/useWorldStore';
import { Coins, Package, TrendingUp, TrendingDown } from 'lucide-react';

export const SettlementInspector: React.FC = () => {
    const selectedHex = useWorldStore(state => state.selectedHex);

    if (!selectedHex || (!selectedHex.settlement_name && selectedHex.biome_tag !== 'SETTLEMENT')) {
        return null;
    }

    const market = selectedHex.market_state || {};
    const resources = Object.entries(market) as [string, any][];

    return (
        <div className="absolute right-4 top-24 w-80 bg-slate-900/90 border border-amber-500/30 rounded-lg p-4 text-slate-200 shadow-2xl backdrop-blur-md">
            <div className="flex items-center gap-2 mb-4 border-b border-amber-500/50 pb-2">
                <div className="p-2 bg-amber-500/20 rounded-lg">
                    <Coins className="text-amber-400 w-5 h-5" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-amber-200 uppercase tracking-wider">
                        {selectedHex.settlement_name || "Outpost"}
                    </h3>
                    <p className="text-xs text-slate-400">Economic Hub</p>
                </div>
            </div>

            <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400 flex items-center gap-1">
                        <TrendingUp className="w-4 h-4 text-green-400" /> Production
                    </span>
                    <span className="font-mono text-green-400">+{selectedHex.production_rate || 0}</span>
                </div>

                <div className="mt-4">
                    <h4 className="text-xs font-bold text-slate-500 uppercase mb-2 flex items-center gap-1">
                        <Package className="w-3 h-3" /> Market Inventory
                    </h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                        {resources.length > 0 ? resources.map(([item, supplyObj]) => {
                            const supply = typeof supplyObj === 'number' ? supplyObj : (supplyObj?.supply || 0);
                            return (
                                <div key={item} className="flex items-center justify-between bg-white/5 p-2 rounded border border-white/5 hover:border-amber-500/20 transition-colors">
                                    <span className="text-sm capitalize text-slate-300">{item.replace('_', ' ')}</span>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-sm font-mono ${supply >= 0 ? 'text-blue-400' : 'text-red-400'}`}>
                                            {supply.toFixed(1)}
                                        </span>
                                        {supply < 0 && <TrendingDown className="w-3 h-3 text-red-400 animate-pulse" />}
                                    </div>
                                </div>
                            );
                        }) : (
                            <p className="text-xs text-slate-600 italic">No resources available for trade.</p>
                        )}
                    </div>
                </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between uppercase tracking-tighter">
                <span>Supply/Demand Loop: Stable</span>
                <span className="text-amber-500/50">SAGA v1.0</span>
            </div>
        </div>
    );
};
