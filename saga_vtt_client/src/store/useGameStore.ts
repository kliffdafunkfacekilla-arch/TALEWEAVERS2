import { create } from 'zustand';

import { useCombatStore } from './useCombatStore';
import { useCharacterStore } from './useCharacterStore';

// ── Type Definitions ──────────────────────────────────────────────────

export type VTTTier = 1 | 2 | 3 | 4 | 5;

export interface ChatMessage {
    sender: 'SYSTEM' | 'AI_DIRECTOR' | 'PLAYER' | 'NARRATOR' | 'ERROR';
    text: string;
}

export interface MapToken {
    id: string;
    label: string;
    x: number;
    y: number;
    tint: number;
    isPlayer: boolean;
    avatar_sprite?: {
        sheet_url: string;
        x: number;
        y: number;
        w: number;
        h: number;
    };
}

export interface LoadoutItem {
    id: string;
    name: string;
    type: 'MELEE' | 'RANGED' | 'MAGIC' | 'MOBILITY' | 'SOCIAL' | 'UTILITY' | 'CONSUMABLE';
    target: string;
    range: number;
    stamina_cost?: number;
    focus_cost?: number;
    dice?: string;
    desc: string;
    lead_stat?: string;
    trail_stat?: string;
    skill_rank?: number;
    target_dc?: number;
}

export interface QuestItem {
    id: string;
    title: string;
    completed: boolean;
    target_node_id?: string;
}

export interface InventorySlot {
    id: number;
    itemName: string | null;
}

export interface SurvivalJob {
    characterName: string;
    jobName: 'FORAGE' | 'GUARD' | 'FIRE' | 'REST' | 'REPAIR';
}

export interface ExplorationNode {
    id: string;
    label: string;
    x: number;
    y: number;
    type: 'POI' | 'TRANSITION' | 'DANGER' | 'RESOURCE';
    connections: string[];
    visual_url?: string; // New: Hex-specific background texture
}

export interface ClientGameState {
    vttTier: VTTTier;
    setVttTier: (tier: VTTTier) => void;

    currentScreen: string;
    setScreen: (screen: string) => void;

    activeCampaignId: string | null;
    setCampaignId: (id: string) => void;
    currentHexId: number | null;
    setPlayerHex: (hexId: number) => void;

    survivalJobs: SurvivalJob[];
    assignSurvivalJob: (character: string, job: SurvivalJob['jobName']) => void;
    rations: number;
    fuel: number;
    setSurvivalResources: (rations: number, fuel: number) => void;

    explorationNodes: ExplorationNode[];
    currentNodeId: string | null;
    setExplorationNodes: (nodes: ExplorationNode[]) => void;
    moveNode: (nodeId: string) => void;

    // Narrative & World Engagement
    weather: string;
    tension: number;
    chaosNumbers: number[]; // New: Active chaos strike targets
    currentSagaStage: string;
    pacingProgress: { current: number; goal: number };
    visualAssets: Record<string, string>; // New: asset_id -> url

    ui_locked: boolean;
    chat_log: ChatMessage[];
    map_tokens: MapToken[];
    selectedTokenId: string | null;
    quests: QuestItem[];
    inventory_slots: InventorySlot[];

    sendAction: (action: string, burn: number, target: string) => void;
    executeAction: (skillName: string, targetId: string) => Promise<void>;
    addChatMessage: (msg: ChatMessage) => void;
    selectToken: (id: string | null) => void;
    toggleQuestComplete: (id: string) => void;
    setUiLocked: (locked: boolean) => void;
    injectTierContext: (tier: VTTTier) => Promise<void>;

    characterSheet?: any;
    syncCombatState?: (state: any) => void;
    attributes?: any;

    clientLoadout: LoadoutItem[];
    setClientLoadout: (loadout: LoadoutItem[]) => void;

    campaignSettings: any;
    setCampaignSettings: (settings: any) => void;
}

const INITIAL_STATE: Omit<ClientGameState,
    'sendAction' | 'executeAction' | 'addChatMessage' | 'selectToken' | 'toggleQuestComplete' | 'setUiLocked' | 'setScreen' | 'setCampaignId' | 'setPlayerHex' | 'setVttTier' | 'assignSurvivalJob' | 'setSurvivalResources' | 'setExplorationNodes' | 'moveNode' | 'injectTierContext' | 'setClientLoadout' | 'setCampaignSettings'
> = {
    vttTier: 1, // Start at World Scale
    currentScreen: 'MAIN_MENU',
    activeCampaignId: null,
    currentHexId: 402,

    survivalJobs: [],
    rations: 10,
    fuel: 5,

    explorationNodes: [],
    currentNodeId: null,

    weather: 'Loading weather...',
    tension: 0,
    chaosNumbers: [],
    currentSagaStage: 'Prologue',
    pacingProgress: { current: 0, goal: 2 },
    visualAssets: {},

    ui_locked: false,
    chat_log: [],
    map_tokens: [
        { id: 'player_1', label: 'Kael', x: 5, y: 5, tint: 0x4ade80, isPlayer: true },
    ],
    selectedTokenId: null,
    quests: [
        { id: 'q1', title: 'Reach the Waystation', completed: false },
    ],
    inventory_slots: [
        { id: 1, itemName: 'Steel Rapier' },
        { id: 2, itemName: 'Traveler\'s Bread' },
    ],
    clientLoadout: [],
    campaignSettings: null,
};

export const useGameStore = create<ClientGameState>((set, get) => ({
    ...INITIAL_STATE,

    setVttTier: (tier) => set({ vttTier: tier }),
    setPlayerHex: (hexId: number) => set({ currentHexId: hexId }),
    setScreen: (screen) => set({ currentScreen: screen }),
    setCampaignId: (id) => set({ activeCampaignId: id }),
    setClientLoadout: (loadout) => set({ clientLoadout: loadout }),
    setCampaignSettings: (settings) => set({ campaignSettings: settings }),

    assignSurvivalJob: (character, job) => set((s) => ({
        survivalJobs: [...s.survivalJobs.filter(j => j.characterName !== character), { characterName: character, jobName: job }]
    })),
    setSurvivalResources: (rations, fuel) => set({ rations, fuel }),

    setExplorationNodes: (nodes) => set({ explorationNodes: nodes }),
    moveNode: (nodeId) => set({ currentNodeId: nodeId }),

    addChatMessage: (msg) => set((s) => ({ chat_log: [...s.chat_log, msg] })),
    selectToken: (id) => set({ selectedTokenId: id }),
    toggleQuestComplete: (id) => set((s) => ({
        quests: s.quests.map((q) => q.id === id ? { ...q, completed: !q.completed } : q),
    })),
    setUiLocked: (locked) => set({ ui_locked: locked }),

    sendAction: async (action, _burn, target) => {
        const state = get();
        if (state.ui_locked) return;

        set({ ui_locked: true });

        const payload = {
            campaign_id: state.activeCampaignId || 'CAMPAIGN_001',
            player_id: 'PLAYER_001',
            player_input: action === "TRAVEL" ? `Move to ${target}` : action,
        };

        try {
            const directorUrl = import.meta.env.VITE_SAGA_DIRECTOR_URL || 'http://localhost:8050';
            const res = await fetch(`${directorUrl}/api/campaign/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Action failed");
            const update = await res.json();

            // Update complex state from Director response
            if (update.narration) {
                set((s) => ({
                    chat_log: [
                        ...s.chat_log,
                        { sender: 'AI_DIRECTOR', text: update.narration },
                    ]
                }));
            }

            // Sync mechanical updates
            if (update.updated_vitals) useCharacterStore.getState().setPlayerVitals(update.updated_vitals);
            if (update.current_hex !== undefined) get().setPlayerHex(update.current_hex);

            // New World State Sync
            if (update.weather) set({ weather: update.weather });
            if (update.tension !== undefined) set({ tension: update.tension });

            // Normalize chaos_numbers to array
            if (update.chaos_numbers !== undefined && update.chaos_numbers !== null) {
                if (Array.isArray(update.chaos_numbers)) {
                    set({ chaosNumbers: update.chaos_numbers });
                } else if (typeof update.chaos_numbers === 'number') {
                    set({ chaosNumbers: [update.chaos_numbers] });
                } else if (typeof update.chaos_numbers === 'string') {
                    try {
                        const parsed = JSON.parse(update.chaos_numbers);
                        set({ chaosNumbers: Array.isArray(parsed) ? parsed : [parsed] });
                    } catch {
                        set({ chaosNumbers: [] });
                    }
                }
            }

            if (update.saga_stage) set({ currentSagaStage: update.saga_stage });
            if (update.pacing) set({ pacingProgress: update.pacing });
            if (update.visual_assets) set({ visualAssets: update.visual_assets });

            if (update.active_encounter) {
                // Determine biome for data injection
                let encounterBiome = update.active_encounter.metadata?.biome
                    || update.initial_state?.weather
                    || get().weather;
                if (!encounterBiome || encounterBiome === "Clear Skies") encounterBiome = "FOREST";

                const normalizedEncounter = {
                    ...update.active_encounter,
                    gridWidth: update.active_encounter.gridWidth ?? (update.active_encounter.grid && update.active_encounter.grid.length > 0 ? update.active_encounter.grid[0].length : 15),
                    gridHeight: update.active_encounter.gridHeight ?? (update.active_encounter.grid ? update.active_encounter.grid.length : 10),
                    // Inject missing data structure if needed
                    data: update.active_encounter.data || {
                        category: update.active_encounter.encounter_id === "error_fallback" ? "AMBIENT" : (update.active_encounter.metadata?.type || "COMBAT"),
                        status: "ACTIVE",
                        participants: [],
                        win_condition: "Survive",
                        difficulty: "Standard"
                    },
                    // Ensure tokens have required fields
                    tokens: (update.active_encounter.tokens || []).map((t: any) => ({
                        ...t,
                        current_hp: t.current_hp ?? 10,
                        max_hp: t.max_hp ?? 10
                    }))
                };
                useCombatStore.getState().setActiveEncounter(normalizedEncounter);
            } else {
                const currentEncounter = useCombatStore.getState().activeEncounter;
                if (currentEncounter) {
                    const hexId = get().currentHexId;
                    if (hexId) useCombatStore.getState().markEncounterCleared(hexId.toString());
                    useCombatStore.getState().setActiveEncounter(null);
                }
            }

        } catch (err) {
            console.error(err);
            set({ chat_log: [...get().chat_log, { sender: 'ERROR', text: 'Communication with Saga Director lost.' }] });
        } finally {
            set({ ui_locked: false });
        }
    },

    executeAction: async (skillName, targetId) => {
        const state = get();
        if (state.ui_locked) return;

        const combatState = useCombatStore.getState();
        const activeEncounter = combatState.activeEncounter;
        const targetToken = activeEncounter?.tokens?.find((t: any) => t.id === targetId);

        const targetName = targetToken ? targetToken.name : 'Unknown Target';

        // Translates HUD button clicks into Director actions
        const actionText = `I use ${skillName} against ${targetName} (ID: ${targetId}).`;

        // Send it via the unified sendAction which routes to the Director
        // We use 0 for burn right now, as the backend calculates it
        get().sendAction(actionText, 0, targetId);
    },

    injectTierContext: async (tier) => {
        const tierNames = ["WORLD", "REGIONAL", "LOCAL", "PLAYER"];
        const name = tierNames[tier - 1] || "WORLD";
        get().addChatMessage({ sender: 'AI_DIRECTOR', text: `[PROJECTION SHIFT] Scaling to ${name} level...` });
        const prompt = `The perspective scales down to ${name} level. Describe the environmental focus shifting.`;
        get().sendAction(prompt, 0, "");
    },
}));
