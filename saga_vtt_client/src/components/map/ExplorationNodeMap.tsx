import { useState, useEffect } from 'react';
import { useGameStore, type ExplorationNode } from '../../store/useGameStore';
import { MapPin, ArrowRight, Info, AlertTriangle, Hammer, Target } from 'lucide-react';

export function ExplorationNodeMap() {
    const { explorationNodes, currentNodeId, moveNode, addChatMessage, quests } = useGameStore();
    const [localNodes, setLocalNodes] = useState<ExplorationNode[]>([]);

    // Get active quest targets for highlighting
    const activeQuestTargets = quests
        .filter(q => !q.completed && q.target_node_id)
        .map(q => q.target_node_id);

    // Mock initial nodes if none exist for dev/testing
    useEffect(() => {
        if (explorationNodes.length === 0) {
            const mockNodes: ExplorationNode[] = [
                { id: 'node_1', label: 'Crashed Caravan', x: 200, y: 150, type: 'POI', connections: ['node_2', 'node_3'] },
                { id: 'node_2', label: 'Jagged Ridge', x: 450, y: 100, type: 'DANGER', connections: ['node_1', 'node_4'] },
                { id: 'node_3', label: 'Exposed Vein', x: 300, y: 350, type: 'RESOURCE', connections: ['node_1', 'node_4'] },
                { id: 'node_4', label: 'Cave Entrance', x: 600, y: 300, type: 'TRANSITION', connections: ['node_2', 'node_3'] },
            ];
            setLocalNodes(mockNodes);
        } else {
            setLocalNodes(explorationNodes);
        }
    }, [explorationNodes]);

    const handleNodeClick = (nodeId: string) => {
        const node = localNodes.find(n => n.id === nodeId);
        if (!node) return;

        if (currentNodeId && !node.connections.includes(currentNodeId) && nodeId !== currentNodeId) {
            addChatMessage({ sender: 'SYSTEM', text: `You cannot reach ${node.label} from here.` });
            return;
        }

        const isQuestTarget = activeQuestTargets.includes(nodeId);
        moveNode(nodeId);

        if (isQuestTarget) {
            addChatMessage({ sender: 'AI_DIRECTOR', text: `You approach the objective: ${node.label}. The weight of your task settles in.` });
        } else {
            addChatMessage({ sender: 'AI_DIRECTOR', text: `You move towards the ${node.label}. The terrain becomes difficult.` });
        }
    };

    const getNodeIcon = (type: ExplorationNode['type'], isQuestTarget: boolean) => {
        if (isQuestTarget) return <Target className="w-5 h-5 text-cyan-400 animate-pulse" />;

        switch (type) {
            case 'POI': return <Info className="w-5 h-5 text-blue-400" />;
            case 'DANGER': return <AlertTriangle className="w-5 h-5 text-red-500" />;
            case 'RESOURCE': return <Hammer className="w-5 h-5 text-emerald-400" />;
            case 'TRANSITION': return <ArrowRight className="w-5 h-5 text-amber-400" />;
            default: return <MapPin className="w-5 h-5 text-zinc-400" />;
        }
    };

    return (
        <div className="relative w-full h-full bg-zinc-950 overflow-hidden flex items-center justify-center border border-zinc-900 rounded-sm">
            {/* Rich Biome Background */}
            {currentNodeId && localNodes.find(n => n.id === currentNodeId)?.visual_url && (
                <div
                    className="absolute inset-0 opacity-40 transition-opacity duration-1000"
                    style={{
                        backgroundImage: `url(${localNodes.find(n => n.id === currentNodeId)?.visual_url})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        filter: 'grayscale(30%) contrast(120%)'
                    }}
                />
            )}

            {/* Grid Overlay */}
            <div className="absolute inset-0 opacity-10 pointer-events-none"
                style={{ backgroundImage: 'radial-gradient(circle, #333 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            {/* SVG Connections Layer */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
                {localNodes.map(node =>
                    node.connections.map(connId => {
                        const target = localNodes.find(n => n.id === connId);
                        if (!target || node.id > target.id) return null; // Avoid double lines
                        return (
                            <line
                                key={`${node.id}-${target.id}`}
                                x1={node.x} y1={node.y}
                                x2={target.x} y2={target.y}
                                stroke={activeQuestTargets.includes(node.id) || activeQuestTargets.includes(target.id) ? "#164e63" : "#27272a"}
                                strokeWidth={activeQuestTargets.includes(node.id) || activeQuestTargets.includes(target.id) ? "3" : "2"}
                                strokeDasharray={activeQuestTargets.includes(node.id) || activeQuestTargets.includes(target.id) ? "0" : "4 4"}
                                style={{ transition: 'all 0.5s ease' }}
                            />
                        );
                    })
                )}
            </svg>

            {/* Nodes Layer */}
            {localNodes.map(node => {
                const isQuestTarget = activeQuestTargets.includes(node.id);
                return (
                    <button
                        key={node.id}
                        onClick={() => handleNodeClick(node.id)}
                        className={`absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-2 group transition-all duration-300 ${currentNodeId === node.id ? 'scale-110' : 'hover:scale-105'
                            }`}
                        style={{ left: node.x, top: node.y }}
                    >
                        <div className={`p-3 rounded-full border-2 transition-all ${currentNodeId === node.id
                            ? 'bg-zinc-800 border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.5)]'
                            : isQuestTarget
                                ? 'bg-cyan-950/40 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                                : 'bg-zinc-900 border-zinc-800 group-hover:border-zinc-500'
                            }`}>
                            {getNodeIcon(node.type, isQuestTarget)}
                        </div>
                        <div className="flex flex-col items-center">
                            <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded shadow-lg ${currentNodeId === node.id
                                ? 'bg-amber-500 text-black'
                                : isQuestTarget
                                    ? 'bg-cyan-600 text-cyan-50'
                                    : 'text-zinc-500 bg-black/50'
                                }`}>
                                {node.label}
                            </span>
                            {isQuestTarget && !currentNodeId === node.id && (
                                <span className="text-[8px] text-cyan-400 font-bold uppercase tracking-tighter mt-1 drop-shadow-md">Active Objective</span>
                            )}
                        </div>
                    </button>
                );
            })}

            {/* Scale Indicator */}
            <div className="absolute bottom-4 left-4 flex flex-col gap-1">
                <div className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest italic">Local Exploration Overlay</div>
                <div className="w-32 h-1 bg-zinc-800 rounded-full flex overflow-hidden">
                    <div className="w-1/4 h-full bg-zinc-600" />
                </div>
                <div className="text-[8px] font-bold text-zinc-700 uppercase">TIER 4 — NODE SCALE [1 HEX]</div>
            </div>

            {/* Legend */}
            <div className="absolute bottom-4 right-4 bg-black/60 backdrop-blur-sm border border-zinc-800 p-3 rounded flex flex-col gap-2">
                <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                    <div className="w-3 h-3 rounded-full bg-cyan-500 animate-pulse" /> Quest Objective
                </div>
                <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                    <div className="w-2 h-2 rounded-full bg-blue-400" /> Point of Interest
                </div>
                <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                    <div className="w-2 h-2 rounded-full bg-red-500" /> Danger Zone
                </div>
                <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" /> Resource Node
                </div>
                <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                    <div className="w-2 h-2 rounded-full bg-amber-400" /> Exit / Transition
                </div>
            </div>
        </div>
    );
}
