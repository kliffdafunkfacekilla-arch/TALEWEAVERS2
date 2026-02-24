import { create } from 'zustand';

// ── Type Definitions ──────────────────────────────────────────────────
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
}

export interface Injuries {
    body: string[];
    mind: string[];
}

export interface ChatMessage {
    sender: 'SYSTEM' | 'AI_DIRECTOR' | 'PLAYER';
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

export interface ClientGameState {
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

    // 12 Core Attributes
    attributes: CoreAttributes;

    // Dual-Track Injuries
    injuries: Injuries;

    // Director's Log / Chat
    chat_log: ChatMessage[];

    // Available Skills for the Action Deck
    skills: string[];

    // Map Tokens
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
}

// ── Mock Data for Visual Development ──────────────────────────────────
const MOCK_STATE: Omit<ClientGameState,
    'sendAction' | 'addChatMessage' | 'selectToken' | 'toggleQuestComplete' | 'setUiLocked'
> = {
    ui_locked: false,
    characterName: 'Kael Thornwood',

    vitals: {
        hp: { current: 18, max: 24 },
        stamina: { current: 8, max: 12 },
        focus: { current: 6, max: 9 },
        composure: { current: 10, max: 14 },
    },

    attributes: {
        might: 7, endurance: 5, vitality: 6, fortitude: 4, reflexes: 8, finesse: 3,
        knowledge: 4, logic: 5, charm: 3, willpower: 6, awareness: 5, intuition: 4,
    },

    injuries: {
        body: ['Fractured Rib'],
        mind: [],
    },

    chat_log: [
        { sender: 'SYSTEM', text: 'Campaign loaded: "The Shattered Wastes"' },
        { sender: 'AI_DIRECTOR', text: 'The wind howls across the broken plains. Ahead, a cluster of twisted trees marks the old waystation. Something moves in the shadows between the trunks.' },
        { sender: 'PLAYER', text: 'I draw my blade and advance cautiously toward the treeline.' },
        { sender: 'AI_DIRECTOR', text: 'A low growl rumbles from behind a collapsed stone wall. Two pairs of amber eyes glow in the darkness. The pack wolves have found you.' },
        { sender: 'SYSTEM', text: '⚔️ Encounter initiated — 2× Ashland Wolves' },
    ],

    skills: ['Assault', 'Coercion', 'Mobility', 'Precise Shot', 'Endure', 'Deceive'],

    map_tokens: [
        { id: 'player_1', label: 'Kael', x: 5, y: 5, tint: 0x4ade80, isPlayer: true },
        { id: 'wolf_01', label: 'Wolf', x: 7, y: 4, tint: 0xef4444, isPlayer: false },
        { id: 'wolf_02', label: 'Wolf', x: 8, y: 6, tint: 0xef4444, isPlayer: false },
    ],

    selectedTokenId: null,

    quests: [
        { id: 'q1', title: 'Reach the Waystation', completed: true },
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
    ...MOCK_STATE,

    sendAction: (action: string, burn: number, target: string) => {
        const state = get();
        if (state.ui_locked) return;

        // Lock the UI immediately
        set({ ui_locked: true });

        // Log the outgoing action
        const payload = { action, burn, target };
        console.log('[VTT] Action sent:', JSON.stringify(payload));

        // Add a system message showing the action
        set((s) => ({
            chat_log: [
                ...s.chat_log,
                { sender: 'SYSTEM' as const, text: `▶ ${action} (Burn: ${burn}) → ${target}` },
            ],
        }));

        // Simulate backend response after 2 seconds
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
