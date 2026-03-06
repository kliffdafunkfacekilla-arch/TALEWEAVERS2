import { create } from 'zustand';

export interface HexCell {
    id: number;
    x: number;
    y: number;
    neighbors: number[];
    elevation: number;
    temperature: number;
    moisture: number;
    wind_dx: number;
    wind_dy: number;
    biome_tag: string;
    faction_owner: string;
    settlement_name: string;
    has_river: boolean;
    road_next_id: number;
    available_resources: Record<string, string>;
    local_resources: string[];
    local_fauna: string[];
    local_flora: string[];
    threat_level: number;
    market_state?: Record<string, number>;
    production_rate?: number;
}

export interface WorldData {
    metadata: {
        world_name: string;
        map_type: string;
        cell_count: number;
    };
    time_rules: any;
    factions: any;
    macro_map: HexCell[];
    road_network: any[];
}

export interface LocalNode {
    id: number;
    x: number;
    y: number;
    elevation: number;
    moisture: number;
    biome: string;
    settlement: string;
    market_state?: Record<string, number>;
}

interface WorldState {
    worldData: WorldData | null;
    loadedHexes: HexCell[];
    viewLens: 'PHYSICAL' | 'POLITICAL' | 'RESOURCE' | 'THREAT';
    selectedHex: HexCell | null;
    subGridNodes: LocalNode[];
    editMode: string;
    activeBrush: string | number;
    brushSize: number;
    brushStrength: number;

    worldHistory: any[];
    setWorldData: (data: WorldData) => void;
    fetchMapChunk: (x: number, y: number, radius: number) => Promise<void>;
    clearWorld: () => void;
    setViewLens: (lens: WorldState['viewLens']) => void;
    setSelectedHex: (hex: HexCell | null) => void;
    fetchSubGrid: (hexId: number) => Promise<void>;
    fetchHistory: () => Promise<void>;
    setEditMode: (mode: string) => void;
    setActiveBrush: (brush: string | number) => void;
    setBrushSize: (size: number) => void;
    setBrushStrength: (strength: number) => void;
    paintHex: (hexIndex: number) => void;
}

export const useWorldStore = create<WorldState>((set) => ({
    worldData: null,
    loadedHexes: [],
    viewLens: 'PHYSICAL',
    selectedHex: null,
    subGridNodes: [],
    editMode: 'NONE',
    activeBrush: '',
    brushSize: 1,
    brushStrength: 100,
    worldHistory: [],

    setWorldData: (data) => set({ worldData: data, loadedHexes: data.macro_map || [] }),

    fetchMapChunk: async (x, y, radius) => {
        try {
            const res = await fetch(`${import.meta.env.VITE_SAGA_ARCHITECT_URL || "http://localhost:8002"}/api/world/chunk?x=${x}&y=${y}&radius=${radius}`);
            if (!res.ok) throw new Error("Chunk fetch failed");
            const update = await res.json();

            set((state) => {
                const existingIds = new Set(state.loadedHexes.map(h => h.id));
                const newHexes = update.world_data.macro_map.filter((h: any) => !existingIds.has(h.id));

                return {
                    loadedHexes: [...state.loadedHexes, ...newHexes]
                };
            });
        } catch (err) {
            console.error("[WORLD_STORE] Chunk fetch error:", err);
        }
    },

    clearWorld: () => set({ worldData: null, loadedHexes: [] }),

    setViewLens: (lens) => set({ viewLens: lens }),

    setSelectedHex: (hex) => set({ selectedHex: hex }),

    fetchSubGrid: async (hexId) => {
        try {
            const res = await fetch(`${import.meta.env.VITE_SAGA_ARCHITECT_URL || "http://localhost:8002"}/api/world/subgrid/${hexId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    config: {
                        geography: { hex_count: 2000, plate_count: 12, heightmap_steps: [] },
                        climate: { north_pole: [-10, 5], equator: [25, 35], south_pole: [-10, 5], wind_bands: [], rain_multiplier: 1.0 },
                        ecology: { biomes: [], resources: [], global_life: [] },
                        society: { factions: [], cultures: [], religions: [], building_templates: [] }
                    },
                    sim_ticks: 100
                })
            });
            if (!res.ok) throw new Error("Subgrid fetch failed");
            const data = await res.json();

            set({ subGridNodes: data.subgrid.macro_map || [] });
        } catch (err) {
            console.error("[WORLD_STORE] Subgrid fetch error:", err);
            set({ subGridNodes: [] });
        }
    },

    fetchHistory: async () => {
        try {
            const res = await fetch(`${import.meta.env.VITE_SAGA_ARCHITECT_URL || "http://localhost:8002"}/api/world/history`);
            if (!res.ok) throw new Error("History fetch failed");
            const data = await res.json();
            set({ worldHistory: data.history || [] });
        } catch (err) {
            console.error("[WORLD_STORE] History fetch error:", err);
            set({ worldHistory: [] });
        }
    },

    setEditMode: (mode) => set({ editMode: mode }),
    setActiveBrush: (brush) => set({ activeBrush: brush }),
    setBrushSize: (size) => set({ brushSize: size }),
    setBrushStrength: (strength) => set({ brushStrength: strength }),

    paintHex: (hexIndex) => set((state) => {
        if (!state.worldData || state.editMode === 'NONE') return state;
        const newMap = [...state.worldData.macro_map];

        const targetHex = newMap[hexIndex];
        if (!targetHex) return state;

        const paintedIds = new Set<number>();
        const queue: { id: number, dist: number }[] = [{ id: targetHex.id, dist: 1 }];

        while (queue.length > 0) {
            const current = queue.shift()!;
            if (paintedIds.has(current.id)) continue;
            paintedIds.add(current.id);

            if (current.dist < state.brushSize) {
                const cell = newMap.find((h: any) => h.id === current.id);
                if (cell && cell.neighbors) {
                    cell.neighbors.forEach((nId: number) => {
                        if (!paintedIds.has(nId)) {
                            queue.push({ id: nId, dist: current.dist + 1 });
                        }
                    });
                }
            }
        }

        for (let i = 0; i < newMap.length; i++) {
            if (paintedIds.has(newMap[i].id)) {
                if (state.brushStrength < 100) {
                    if (Math.random() * 100 > state.brushStrength) continue;
                }

                const cell = { ...newMap[i] };
                if (state.editMode === 'ELEVATION') {
                    cell.elevation = state.activeBrush as number;
                    if (cell.elevation <= 0.2) { cell.biome_tag = 'OCEAN'; cell.faction_owner = ''; }
                    else if (cell.biome_tag === 'OCEAN') { cell.biome_tag = 'WASTELAND'; }
                }
                else if (state.editMode === 'BIOME') { cell.biome_tag = state.activeBrush as string; }
                else if (state.editMode === 'FACTION') { cell.faction_owner = state.activeBrush === 'UNCLAIMED' ? '' : state.activeBrush as string; }
                else if (state.editMode === 'RESOURCE') {
                    if (!cell.local_resources) cell.local_resources = [];
                    if (!cell.local_resources.includes(state.activeBrush as string)) {
                        cell.local_resources = [...cell.local_resources, state.activeBrush as string];
                    } else {
                        cell.local_resources = cell.local_resources.filter((r: string) => r !== state.activeBrush);
                    }
                }
                else if (state.editMode === 'FAUNA') {
                    if (!cell.local_fauna) cell.local_fauna = [];
                    if (!cell.local_fauna.includes(state.activeBrush as string)) {
                        cell.local_fauna = [...cell.local_fauna, state.activeBrush as string];
                    } else {
                        cell.local_fauna = cell.local_fauna.filter((r: string) => r !== state.activeBrush);
                    }
                }
                else if (state.editMode === 'FLORA') {
                    if (!cell.local_flora) cell.local_flora = [];
                    if (!cell.local_flora.includes(state.activeBrush as string)) {
                        cell.local_flora = [...cell.local_flora, state.activeBrush as string];
                    } else {
                        cell.local_flora = cell.local_flora.filter((r: string) => r !== state.activeBrush);
                    }
                }
                newMap[i] = cell;
            }
        }

        return {
            worldData: { ...state.worldData, macro_map: newMap },
            selectedHex: state.selectedHex?.id === targetHex.id ? newMap.find((c: any) => c.id === targetHex.id) : state.selectedHex
        };
    }),
}));
