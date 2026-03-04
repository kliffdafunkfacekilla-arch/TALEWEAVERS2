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
}

const INITIAL_STATE: Omit<ClientGameState,
    'sendAction' | 'executeAction' | 'addChatMessage' | 'selectToken' | 'toggleQuestComplete' | 'setUiLocked' | 'setScreen' | 'setCampaignId' | 'setPlayerHex' | 'setVttTier' | 'assignSurvivalJob' | 'setSurvivalResources' | 'setExplorationNodes' | 'moveNode' | 'injectTierContext'
> = {
    vttTier: 2,
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
};

export const useGameStore = create<ClientGameState>((set, get) => ({
    ...INITIAL_STATE,

    setVttTier: (tier) => set({ vttTier: tier }),
    setPlayerHex: (hexId: number) => set({ currentHexId: hexId }),
    setScreen: (screen) => set({ currentScreen: screen }),
    setCampaignId: (id) => set({ activeCampaignId: id }),

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
            const res = await fetch('http://localhost:8000/api/campaign/action', {
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
            if (update.chaos_numbers) set({ chaosNumbers: update.chaos_numbers });
            if (update.saga_stage) set({ currentSagaStage: update.saga_stage });
            if (update.pacing) set({ pacingProgress: update.pacing });
            if (update.visual_assets) set({ visualAssets: update.visual_assets });

            if (update.active_encounter) {
                useCombatStore.getState().setActiveEncounter(update.active_encounter);
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
        set({ ui_locked: true });

        try {
            const combatState = useCombatStore.getState();
            const charState = useCharacterStore.getState();

            const activeEncounter = combatState.activeEncounter;
            const targetToken = activeEncounter?.tokens?.find((t: any) => t.id === targetId);

            let skillRank = 0;
            if (charState.characterSheet?.tactical_skills) {
                const skillData = charState.characterSheet.tactical_skills[skillName];
                skillRank = typeof skillData === 'object' ? skillData.rank : (typeof skillData === 'number' ? skillData : 0);
            }

            const skillToStatMap: Record<string, string> = {
                'Assault': 'might', 'Ballistics': 'reflexes', 'Fortify': 'fortitude',
                'Mobility': 'finesse', 'Tactics': 'logic', 'Deceive': 'charm',
                'Coercion': 'willpower', 'Basic Attack': 'might', 'Ranged Attack': 'reflexes'
            };
            const leadStat = skillToStatMap[skillName] || 'might';
            const statMod = charState.attributes[leadStat] || 0;

            const playerToken = activeEncounter?.tokens.find(t => t.isPlayer);
            let hasAdvantage = false;

            if (playerToken && targetToken) {
                const isEngaged = (targetToken.engaged_with?.length || 0) > 0;
                if (isEngaged && !targetToken.engaged_with?.includes(playerToken.id)) hasAdvantage = true;
            }

            const payload = {
                campaign_id: state.activeCampaignId,
                skill_name: skillName,
                skill_rank: skillRank,
                stat_mod: statMod,
                has_advantage: hasAdvantage,
                target: { id: targetId, name: targetToken?.name || 'Unknown', type: targetToken?.isPlayer ? 'Player' : 'Enemy' },
                attacker_attributes: charState.attributes,
                attacker_vitals: charState.vitals,
                equipped_items: []
            };

            const res = await fetch('http://localhost:8000/api/player/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("API Action failed.");
            const result = await res.json();

            // Update combat engagement
            if (playerToken && activeEncounter) {
                useCombatStore.getState().setActiveEncounter({
                    ...activeEncounter,
                    tokens: activeEncounter.tokens.map(t => {
                        if (t.id === playerToken.id) return { ...t, engaged_with: [...(t.engaged_with || []), targetId] };
                        if (t.id === targetId) return { ...t, engaged_with: [...(t.engaged_with || []), playerToken.id] };
                        return t;
                    })
                });
            }

            get().addChatMessage({ sender: 'SYSTEM', text: `> ${skillName} vs ${targetToken?.name || 'Target'}: ${result.resolution_text}` });

            if (result.vitals_update) charState.setPlayerVitals(result.vitals_update);
            useCombatStore.getState().syncCombatState(result);

        } catch (e) {
            console.error(e);
            get().addChatMessage({ sender: 'ERROR', text: 'Action failed.' });
        } finally {
            set({ ui_locked: false });
        }
    },

    injectTierContext: async (tier) => {
        const tierNames = ["GLOBAL", "REGIONAL", "SURVIVAL", "EXPLORATION", "TACTICAL"];
        const name = tierNames[tier - 1];
        get().addChatMessage({ sender: 'AI_DIRECTOR', text: `[NARRATIVE SHIFT] Viewing world at ${name} scale...` });
        const prompt = `The perspective shifts to ${name} scale. Describe the atmospheric transition.`;
        get().sendAction(prompt, 0, "");
    },
}));
