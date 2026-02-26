import { create } from 'zustand';

// ── Type Definitions ──────────────────────────────────────────────────

// --- World Architect Types (Matches C++ VoronoiCell output exactly) ---
export interface HexCell {
    id: number;
    x: number;
    y: number;
    neighbors: number[];
    // --- AZGAAR TOPOLOGY & CLIMATE ---
    elevation: number;
    temperature: number;
    moisture: number;
    wind_dx: number;
    wind_dy: number;
    biome_tag: string;

    // --- S.A.G.A. CULTURAL ENGINE ---
    faction_owner: string;
    settlement_name: string;
    has_river: boolean;

    // --- THE FINER DETAILS (Architect's Palette) ---
    available_resources: Record<string, string>; // Legacy
    local_resources: string[];
    local_fauna: string[];
    local_flora: string[];
    threat_level: number;
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

// --- Character Sheet (Matches CompiledCharacterSheet from Port 8003) ---
export interface CharacterSheet {
    name: string;
    attributes: CoreAttributes;
    vitals: {
        max_hp: number;
        max_stamina: number;
        max_composure: number;
        max_focus: number;
        body_injuries: string[];
        mind_injuries: string[];
    };
    evolutions: any;
    passives: { name: string; effect: string }[];
    powers: string[];
    loadout: Record<string, string>;
    holding_fees: { stamina: number; focus: number };
}

// --- Loadout Item (Client-side equipped item for the Action Deck) ---
export interface LoadoutItem {
    id: string;
    name: string;
    type: 'MELEE' | 'RANGED' | 'MAGIC' | 'CONSUMABLE' | 'MOBILITY' | 'SOCIAL' | 'UTILITY';
    target: 'SELF' | 'ADJACENT' | 'RANGED';
    range: number;
    stamina_cost: number;
    dice: string;
    desc: string;
    // Skill check fields (for MOBILITY/SOCIAL/UTILITY routed to Port 8006)
    lead_stat?: string;
    trail_stat?: string;
    skill_rank?: number;
    target_dc?: number;
}

// --- Player VTT Types ---
export interface ResourcePool {
    current: number;
    max: number;
}

export interface CoreAttributes {
    // Sector I: Physical
    might: number;
    endurance: number;
    vitality: number;
    fortitude: number;
    reflexes: number;
    finesse: number;
    // Sector II: Mental
    knowledge: number;
    logic: number;
    charm: number;
    willpower: number;
    awareness: number;
    intuition: number;
    [key: string]: number;
}

export interface Injuries {
    body: string[];
    mind: string[];
}

export interface ChatMessage {
    sender: 'SYSTEM' | 'AI_DIRECTOR' | 'PLAYER' | 'NARRATOR';
    text: string;
}

export interface MapToken {
    id: string;
    label: string;
    x: number;
    y: number;
    tint: number;
    isPlayer: boolean;
}

export interface QuestItem {
    id: string;
    title: string;
    completed: boolean;
}

export interface InventorySlot {
    id: number;
    itemName: string | null;
}

// --- Tactical Encounter Types ---
export interface EncounterToken {
    id: string;
    name: string;
    x: number;
    y: number;
    color: number;
    isPlayer: boolean;
}

export interface ActiveEncounter {
    gridWidth: number;
    gridHeight: number;
    tokens: EncounterToken[];
}

export interface ClientGameState {
    // Navigation
    currentScreen: string;
    setScreen: (screen: string) => void;

    // World Memory (God Engine output)
    worldData: WorldData | null;
    setWorldData: (data: WorldData) => void;
    clearWorld: () => void;

    // Hex Inspector
    selectedHex: HexCell | null;
    setSelectedHex: (hex: HexCell | null) => void;

    // The Architect's Palette: Edit Brush Logic
    editHex: (hexId: number, editMode: string, brushValue: string) => void;

    // Campaign State (Module 8 integration)
    activeCampaignId: string | null;
    setCampaignId: (id: string) => void;

    // Character Sheet (Module 3 — Port 8003 output)
    characterSheet: CharacterSheet | null;
    setCharacterSheet: (sheet: CharacterSheet) => void;

    // Client-side Loadout (items for the Action Deck)
    clientLoadout: LoadoutItem[];
    setClientLoadout: (items: LoadoutItem[]) => void;

    // Tactical Encounter
    activeEncounter: ActiveEncounter | null;
    setActiveEncounter: (encounter: ActiveEncounter | null) => void;
    moveToken: (id: string, newX: number, newY: number) => void;

    // Targeting (the token you are aiming at on the grid)
    selectedTargetId: string | null;
    setTarget: (id: string | null) => void;

    // UI Lock — when true, disable all action buttons (Director is narrating)
    ui_locked: boolean;

    // Character Name
    characterName: string;

    // Vitals (4 pools from the Character Rules Engine)
    vitals: {
        hp: ResourcePool;
        stamina: ResourcePool;
        focus: ResourcePool;
        composure: ResourcePool;
    };
    setPlayerVitals: (apiVitals: Record<string, number>) => void;

    // 12 Core Attributes
    attributes: CoreAttributes;

    // Dual-Track Injuries
    injuries: Injuries;

    // Director's Log / Chat
    chat_log: ChatMessage[];

    // Available Skills for the Action Deck
    skills: string[];

    // Map Tokens (overworld tokens for non-tactical view)
    map_tokens: MapToken[];
    selectedTokenId: string | null;

    // Quest Tracker
    quests: QuestItem[];

    // Quick Inventory (Hedge Charm slots)
    inventory_slots: InventorySlot[];

    // ── Actions ──
    sendAction: (action: string, burn: number, target: string) => void;
    addChatMessage: (msg: ChatMessage) => void;
    selectToken: (id: string | null) => void;
    toggleQuestComplete: (id: string) => void;
    setUiLocked: (locked: boolean) => void;
    addInjury: (track: 'body' | 'mind', injuryName: string) => void;
}

// ── Initial State ─────────────────────────────────────────────────────
const INITIAL_STATE: Omit<ClientGameState,
    'sendAction' | 'addChatMessage' | 'selectToken' | 'toggleQuestComplete' | 'setUiLocked' | 'setScreen' | 'setWorldData' | 'clearWorld' | 'setCampaignId' | 'setSelectedHex' | 'editHex' | 'setActiveEncounter' | 'moveToken' | 'setPlayerVitals' | 'setTarget' | 'setCharacterSheet' | 'setClientLoadout' | 'addInjury'
> = {
    currentScreen: 'MAIN_MENU',
    worldData: null,
    selectedHex: null,
    activeCampaignId: null,
    characterSheet: null,
    clientLoadout: [],
    activeEncounter: null,
    selectedTargetId: null,
    ui_locked: false,
    characterName: 'Kael Thornwood',

    vitals: {
        hp: { current: 20, max: 20 },
        stamina: { current: 12, max: 12 },
        focus: { current: 9, max: 9 },
        composure: { current: 14, max: 14 },
    },

    attributes: {
        might: 7, endurance: 5, vitality: 6, fortitude: 4, reflexes: 8, finesse: 3,
        knowledge: 4, logic: 5, charm: 3, willpower: 6, awareness: 5, intuition: 4,
    },

    injuries: {
        body: [],
        mind: [],
    },

    chat_log: [],

    skills: ['Assault', 'Coercion', 'Mobility', 'Precise Shot', 'Endure', 'Deceive'],

    map_tokens: [
        { id: 'player_1', label: 'Kael', x: 5, y: 5, tint: 0x4ade80, isPlayer: true },
        { id: 'wolf_01', label: 'Wolf', x: 7, y: 4, tint: 0xef4444, isPlayer: false },
        { id: 'wolf_02', label: 'Wolf', x: 8, y: 6, tint: 0xef4444, isPlayer: false },
    ],

    selectedTokenId: null,

    quests: [
        { id: 'q1', title: 'Reach the Waystation', completed: false },
        { id: 'q2', title: 'Survive the wolf ambush', completed: false },
        { id: 'q3', title: 'Find the hidden cache', completed: false },
    ],

    inventory_slots: [
        { id: 1, itemName: 'Mending Salve' },
        { id: 2, itemName: null },
        { id: 3, itemName: null },
    ],
};

// ── Store ─────────────────────────────────────────────────────────────
export const useGameStore = create<ClientGameState>((set, get) => ({
    ...INITIAL_STATE,

    // Navigation
    setScreen: (screen) => set({ currentScreen: screen }),

    // World Memory
    setWorldData: (data) => set({ worldData: data }),
    clearWorld: () => set({ worldData: null }),

    // Hex Inspector
    setSelectedHex: (hex) => set({ selectedHex: hex }),

    // The Architect's Palette Logic
    editHex: (hexId: number, editMode: string, brushValue: string) => set((state) => {
        if (!state.worldData) return state;

        const updatedMap = [...state.worldData.macro_map];
        const cell = { ...updatedMap[hexId] };

        // Initialize missing arrays (just in case)
        if (!cell.local_resources) cell.local_resources = [];
        if (!cell.local_fauna) cell.local_fauna = [];
        if (!cell.local_flora) cell.local_flora = [];

        if (editMode === 'BIOME') {
            cell.biome_tag = brushValue;
        }
        else if (editMode === 'FACTION') {
            cell.faction_owner = brushValue;
        }
        else if (editMode === 'RESOURCE') {
            if (!cell.local_resources.includes(brushValue)) {
                cell.local_resources.push(brushValue);
            } else {
                cell.local_resources = cell.local_resources.filter(r => r !== brushValue);
            }
        }
        else if (editMode === 'FAUNA') {
            if (!cell.local_fauna.includes(brushValue)) {
                cell.local_fauna.push(brushValue);
            } else {
                cell.local_fauna = cell.local_fauna.filter(r => r !== brushValue);
            }
        }
        else if (editMode === 'FLORA') {
            if (!cell.local_flora.includes(brushValue)) {
                cell.local_flora.push(brushValue);
            } else {
                cell.local_flora = cell.local_flora.filter(r => r !== brushValue);
            }
        }

        updatedMap[hexId] = cell;

        return {
            worldData: { ...state.worldData, macro_map: updatedMap },
            selectedHex: state.selectedHex?.id === hexId ? cell : state.selectedHex // Also update the inspector if we're looking at it
        };
    }),

    // Campaign
    setCampaignId: (id) => set({ activeCampaignId: id }),

    // Character Sheet (from Port 8003)
    setCharacterSheet: (sheet) => set({ characterSheet: sheet, characterName: sheet.name }),

    // Client Loadout (for Action Deck)
    setClientLoadout: (items) => set({ clientLoadout: items }),

    // Tactical Encounter
    setActiveEncounter: (encounter) => set({ activeEncounter: encounter }),
    moveToken: (id, newX, newY) => set((state) => {
        if (!state.activeEncounter) return state;
        const updatedTokens = state.activeEncounter.tokens.map(t =>
            t.id === id ? { ...t, x: newX, y: newY } : t
        );
        return { activeEncounter: { ...state.activeEncounter, tokens: updatedTokens } };
    }),

    // Targeting
    setTarget: (id) => set({ selectedTargetId: id }),

    // Vitals — maps API response to all 4 pools
    setPlayerVitals: (apiVitals) => set((state) => ({
        vitals: {
            hp: {
                current: apiVitals.current_hp ?? state.vitals.hp.current,
                max: apiVitals.max_hp ?? state.vitals.hp.max,
            },
            stamina: {
                current: apiVitals.current_stamina ?? apiVitals.stamina ?? state.vitals.stamina.current,
                max: apiVitals.max_stamina ?? state.vitals.stamina.max,
            },
            focus: {
                current: apiVitals.current_focus ?? state.vitals.focus.current,
                max: apiVitals.max_focus ?? state.vitals.focus.max,
            },
            composure: {
                current: apiVitals.current_composure ?? state.vitals.composure.current,
                max: apiVitals.max_composure ?? state.vitals.composure.max,
            },
        }
    })),

    // Dual-Track Injury System — permanently scar the character
    addInjury: (track, injuryName) => set((state) => {
        if (state.injuries[track].length >= 4) return state;
        return {
            injuries: {
                ...state.injuries,
                [track]: [...state.injuries[track], injuryName]
            }
        };
    }),

    sendAction: (action: string, burn: number, target: string) => {
        const state = get();
        if (state.ui_locked) return;

        set({ ui_locked: true });

        const payload = { action, burn, target };
        console.log('[VTT] Action sent:', JSON.stringify(payload));

        set((s) => ({
            chat_log: [
                ...s.chat_log,
                { sender: 'SYSTEM' as const, text: `▶ ${action} (Burn: ${burn}) → ${target}` },
            ],
        }));

        setTimeout(() => {
            set((s) => ({
                ui_locked: false,
                vitals: {
                    ...s.vitals,
                    stamina: {
                        ...s.vitals.stamina,
                        current: Math.max(0, s.vitals.stamina.current - burn),
                    },
                },
                chat_log: [
                    ...s.chat_log,
                    { sender: 'AI_DIRECTOR' as const, text: `The ${target} recoils from your ${action.toLowerCase()}. The blow lands with brutal precision.` },
                ],
            }));
        }, 2000);
    },

    addChatMessage: (msg: ChatMessage) => {
        set((s) => ({ chat_log: [...s.chat_log, msg] }));
    },

    selectToken: (id: string | null) => {
        set({ selectedTokenId: id });
    },

    toggleQuestComplete: (id: string) => {
        set((s) => ({
            quests: s.quests.map((q) =>
                q.id === id ? { ...q, completed: !q.completed } : q
            ),
        }));
    },

    setUiLocked: (locked: boolean) => {
        set({ ui_locked: locked });
    },
}));
