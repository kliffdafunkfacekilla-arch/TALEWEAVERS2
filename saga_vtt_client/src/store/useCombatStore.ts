import { create } from 'zustand';

export interface EncounterToken {
    id: string;
    name: string;
    x: number;
    y: number;
    color: number;
    isPlayer: boolean;
    radius?: number;
    direction?: number; // 0=N, 1=E, 2=S, 3=W
    is_prone?: boolean;
    engaged_with?: string[]; // IDs of tokens this token has clashed with this round
}

export interface ActiveEncounter {
    encounter_id: string;
    tokens: EncounterToken[];
    gridWidth?: number;
    gridHeight?: number;
    grid?: number[][];
    data: {
        category?: string;
        title: string;
        narrative_prompt: string;
        npcs?: any[];
        enemies?: any[];
        trigger_effect?: any;
        options?: any[];
        loot_tags?: string[];
        spatial?: { x_offset: number; y_offset: number; footprint_radius: number };
    };
    interactionHistory: { role: string; content: string }[];
}

interface CombatState {
    activeEncounter: ActiveEncounter | null;
    encountersCleared: Set<string>;
    selectedTargetId: string | null;

    setActiveEncounter: (encounter: ActiveEncounter | null) => void;
    markEncounterCleared: (id: string) => void;
    moveToken: (id: string, newX: number, newY: number) => void;
    setTarget: (id: string | null) => void;
    syncCombatState: (result: any) => void;
}

export const useCombatStore = create<CombatState>((set) => ({
    activeEncounter: null,
    encountersCleared: new Set<string>(),
    selectedTargetId: null,

    setActiveEncounter: (encounter) => set({ activeEncounter: encounter }),

    markEncounterCleared: (id) => set((s) => {
        const next = new Set(s.encountersCleared);
        next.add(id);
        return { encountersCleared: next };
    }),

    moveToken: (id, newX, newY) => set((state) => {
        if (!state.activeEncounter) return state;
        const updatedTokens = state.activeEncounter.tokens.map(t =>
            t.id === id ? { ...t, x: newX, y: newY } : t
        );
        return { activeEncounter: { ...state.activeEncounter, tokens: updatedTokens } };
    }),

    setTarget: (id) => set({ selectedTargetId: id }),

    syncCombatState: (result) => {
        const { new_target_hp, encounter_ended, vitals_update: _vitals, targetId, clash_result } = result;

        if (targetId) {
            set((s) => ({
                activeEncounter: s.activeEncounter ? {
                    ...s.activeEncounter,
                    tokens: s.activeEncounter.tokens.map((t: any) => {
                        if (t.id === targetId) {
                            return {
                                ...t,
                                current_hp: new_target_hp !== undefined ? new_target_hp : t.current_hp,
                                is_prone: clash_result === "CRITICAL_MISS" ? true : t.is_prone
                            };
                        }
                        return t;
                    })
                } : null
            }));
        }

        // vitals_update should be handled by CharacterStore, but we might need a signal here
        // or just let the caller handle multiple stores.

        if (encounter_ended || (new_target_hp !== undefined && new_target_hp <= 0)) {
            set({ activeEncounter: null, selectedTargetId: null });
        }
    },
}));
