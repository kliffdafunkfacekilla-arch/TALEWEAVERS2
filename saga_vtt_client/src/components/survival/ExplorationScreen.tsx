import React from 'react';
import { useGameStore, type ExplorationNode } from '../../store/useGameStore';

export const ExplorationScreen: React.FC = () => {
    const nodes = useGameStore((s) => s.explorationNodes);
    const currentNodeId = useGameStore((s) => s.currentNodeId);
    const setExplorationNodes = useGameStore((s) => s.setExplorationNodes);
    const moveNode = useGameStore((s) => s.moveNode);
    const setVttTier = useGameStore((s) => s.setVttTier);

    // Initial Test Nodes if empty
    React.useEffect(() => {
        if (nodes.length === 0) {
            const testNodes: ExplorationNode[] = [
                { id: 'start', label: 'Forest Path', x: 200, y: 500, type: 'TRANSITION', connections: ['clearing'] },
                { id: 'clearing', label: 'Overgrown Clearing', x: 500, y: 300, type: 'POI', connections: ['start', 'towers'] },
                { id: 'towers', label: 'Crumbling Watchtower', x: 800, y: 200, type: 'DANGER', connections: ['clearing'] }
            ];
            setExplorationNodes(testNodes);
            moveNode('start');
        }
    }, [nodes, setExplorationNodes, moveNode]);

    return (
        <div className="relative w-full h-full bg-zinc-950 overflow-hidden flex flex-col items-center justify-center">
            {/* Exploration Background (Styled Map) */}
            <div
                className="absolute inset-0 bg-cover bg-center opacity-40 grayscale-[0.5] hover:grayscale-0 transition-all duration-700"
                style={{ backgroundImage: `url('/assets/exploration_bg.png')` }}
            />

            {/* SVG Connector Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
                {nodes.map(node => node.connections.map(targetId => {
                    const targetNode = nodes.find(n => n.id === targetId);
                    if (!targetNode) return null;
                    return (
                        <line
                            key={`${node.id}-${targetId}`}
                            x1={node.x} y1={node.y}
                            x2={targetNode.x} y2={targetNode.y}
                            stroke="rgba(251, 191, 36, 0.2)"
                            strokeWidth="2"
                            strokeDasharray="4 4"
                        />
                    );
                }))}
            </svg>

            {/* Clickable Nodes */}
            {nodes.map(node => (
                <button
                    key={node.id}
                    onClick={() => moveNode(node.id)}
                    className={`absolute -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${currentNodeId === node.id
                        ? 'bg-amber-500/20 border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.4)] z-20 scale-110'
                        : 'bg-zinc-900/80 border-zinc-700 hover:border-zinc-400 z-10'
                        }`}
                    style={{ left: node.x, top: node.y }}
                >
                    <div className={`w-3 h-3 rounded-full ${currentNodeId === node.id ? 'bg-amber-500 animate-pulse' : 'bg-zinc-600'}`} />
                    <div className="absolute top-14 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-bold uppercase tracking-widest text-zinc-400 bg-black/80 px-2 py-1 rounded border border-zinc-800">
                        {node.label}
                    </div>
                </button>
            ))}

            {/* Bottom HUD: Status */}
            <div className="absolute bottom-8 left-8 bg-black/80 backdrop-blur-md border border-zinc-800 p-4 rounded-lg">
                <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Current Node</div>
                <div className="text-lg font-bold text-white tracking-tight uppercase">
                    {nodes.find(n => n.id === currentNodeId)?.label || 'Awaiting Input...'}
                </div>
                <div className="mt-4 flex gap-2">
                    <button
                        onClick={() => setVttTier(2)}
                        className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[10px] font-bold uppercase tracking-widest rounded border border-zinc-700"
                    >
                        Return to Map
                    </button>
                </div>
            </div>

            {/* Top Right HUD: Tier Indicator */}
            <div className="absolute top-8 right-8 pointer-events-none text-right">
                <div className="text-sm font-bold text-amber-500/80 tracking-[0.4em] uppercase">Tier 4: Exploration</div>
                <div className="text-[10px] text-zinc-600 italic uppercase">Point-and-Click Node Navigation</div>
            </div>
        </div>
    );
};
