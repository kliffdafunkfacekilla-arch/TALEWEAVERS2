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
    tactical_skills?: Record<string, any>;
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

export interface ClientGameState {
    // Navigation
    currentScreen: string;
    setScreen: (screen: string) => void;

    // World Memory (God Engine output)
    worldData: WorldData | null;
    setWorldData: (data: WorldData) => void;
    clearWorld: () => void;

    // NEW: Map Visual Lenses
    viewLens: 'PHYSICAL' | 'POLITICAL' | 'RESOURCE' | 'THREAT';
    setViewLens: (lens: 'PHYSICAL' | 'POLITICAL' | 'RESOURCE' | 'THREAT') => void;

    // Hex Inspector
    selectedHex: HexCell | null;
    setSelectedHex: (hex: HexCell | null) => void;

    // The Architect's Palette: Edit Brush Logic
    editMode: string;
    setEditMode: (mode: string) => void;
    activeBrush: string | number;
    setActiveBrush: (brush: string | number) => void;
    brushSize: number;
    setBrushSize: (size: number) => void;
    brushStrength: number;
    setBrushStrength: (strength: number) => void;
    paintHex: (hexIndex: number) => void;

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
    encountersCleared: Set<string>;
    setActiveEncounter: (encounter: ActiveEncounter | null) => void;
    markEncounterCleared: (id: string) => void;
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
    executeAction: (skillName: string, targetId: string) => Promise<void>;
    addChatMessage: (msg: ChatMessage) => void;
    selectToken: (id: string | null) => void;
    toggleQuestComplete: (id: string) => void;
    setUiLocked: (locked: boolean) => void;
    addInjury: (track: 'body' | 'mind', injuryName: string) => void;
    syncCombatState: (result: {
        new_target_hp?: number;
        encounter_ended?: boolean;
        vitals_update?: any;
        targetId?: string;
    }) => void;
}

// ── Initial State ─────────────────────────────────────────────────────
const INITIAL_STATE: Omit<ClientGameState,
    'sendAction' | 'executeAction' | 'addChatMessage' | 'selectToken' | 'toggleQuestComplete' | 'setUiLocked' | 'setScreen' | 'setWorldData' | 'clearWorld' | 'setCampaignId' | 'setSelectedHex' | 'setEditMode' | 'setActiveBrush' | 'setBrushSize' | 'setBrushStrength' | 'paintHex' | 'setActiveEncounter' | 'moveToken' | 'setPlayerVitals' | 'setTarget' | 'setCharacterSheet' | 'setClientLoadout' | 'addInjury' | 'setViewLens'
> = {
    viewLens: 'PHYSICAL',
    currentScreen: 'MAIN_MENU',
    worldData: null,
    selectedHex: null,
    activeCampaignId: null,
    editMode: 'NONE',
    activeBrush: '',
    brushSize: 1, // Default 1 hex radius
    brushStrength: 100, // Default 100% application chance

    characterSheet: null,
    clientLoadout: [],
    activeEncounter: null,
    encountersCleared: new Set<string>(),
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

    // Map Lenses
    setViewLens: (lens) => set({ viewLens: lens }),

    // World Memory
    setWorldData: (data) => set({ worldData: data }),
    clearWorld: () => set({ worldData: null }),

    // Hex Inspector
    setSelectedHex: (hex) => set({ selectedHex: hex }),

    // The Architect's Palette Logic
    setEditMode: (mode) => set({ editMode: mode }),
    setActiveBrush: (brush) => set({ activeBrush: brush }),
    setBrushSize: (size) => set({ brushSize: size }),
    setBrushStrength: (strength) => set({ brushStrength: strength }),

    paintHex: (hexIndex) => set((state) => {
        if (!state.worldData || state.editMode === 'NONE') return state;
        const newMap = [...state.worldData.macro_map];

        const targetHex = newMap[hexIndex];
        if (!targetHex) return state;

        // Apply Brush geometrically out to 'brushSize' radius
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

        // Apply mutations to all hexes in the radius
        for (let i = 0; i < newMap.length; i++) {
            if (paintedIds.has(newMap[i].id)) {
                // If brushStrength < 100%, roll a percentage die to see if paint applies
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

    // Campaign
    setCampaignId: (id) => set({ activeCampaignId: id }),

    // Character Sheet (from Port 8003 or CharacterBuilder)
    setCharacterSheet: (sheet) => set({
        characterSheet: sheet,
        characterName: sheet.name,
        attributes: sheet.attributes || get().attributes,
        skills: sheet.tactical_skills ? Object.keys(sheet.tactical_skills) : get().skills,
        vitals: sheet.vitals ? {
            hp: { current: sheet.vitals.max_hp, max: sheet.vitals.max_hp },
            stamina: { current: sheet.vitals.max_stamina, max: sheet.vitals.max_stamina },
            focus: { current: sheet.vitals.max_focus, max: sheet.vitals.max_focus },
            composure: { current: sheet.vitals.max_composure, max: sheet.vitals.max_composure }
        } : get().vitals
    }),

    // Client Loadout (for Action Deck)
    setClientLoadout: (items) => set({ clientLoadout: items }),

    // Tactical Encounter
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

    // Targeting
    setTarget: (id) => set({ selectedTargetId: id }),

    // Vitals — maps API response to all 4 pools
    setPlayerVitals: (apiVitals) => set((state) => ({
        vitals: {
            hp: {
                current: apiVitals.current_hp ?? ((apiVitals.hp as any)?.current) ?? state.vitals.hp.current,
                max: apiVitals.max_hp ?? ((apiVitals.hp as any)?.max) ?? state.vitals.hp.max,
            },
            stamina: {
                current: apiVitals.current_stamina ?? ((apiVitals.stamina as any)?.current) ?? state.vitals.stamina.current,
                max: apiVitals.max_stamina ?? ((apiVitals.stamina as any)?.max) ?? state.vitals.stamina.max,
            },
            focus: {
                current: apiVitals.current_focus ?? ((apiVitals.focus as any)?.current) ?? state.vitals.focus.current,
                max: apiVitals.max_focus ?? ((apiVitals.focus as any)?.max) ?? state.vitals.focus.max,
            },
            composure: {
                current: apiVitals.current_composure ?? ((apiVitals.composure as any)?.current) ?? state.vitals.composure.current,
                max: apiVitals.max_composure ?? ((apiVitals.composure as any)?.max) ?? state.vitals.composure.max,
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

    sendAction: async (action: string, burn: number, target: string) => {
        const state = get();
        if (state.ui_locked) return;

        set({ ui_locked: true });

        const payload = {
            campaign_id: state.activeCampaignId || 'CAMPAIGN_001',
            player_id: 'PLAYER_001',
            player_input: action === "TRAVEL" ? `Move to ${target}` : action,
        };

        console.log('[VTT] Action sent:', JSON.stringify(payload));

        try {
            const res = await fetch('http://localhost:8000/api/campaign/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Action failed");

            const update = await res.json();

            set((s) => ({
                ui_locked: false,
                chat_log: [
                    ...s.chat_log,
                    { sender: 'AI_DIRECTOR' as const, text: update.narration || 'The world awaits.' },
                ],
                // If a new encounter is triggered or an old one is closed
                activeEncounter: update.active_encounter || null
            }));

            // Sync vitals if returned
            if (update.updated_vitals) {
                get().setPlayerVitals(update.updated_vitals);
            }

            // Sync Victory logic if encounter closed via chat
            if (!update.active_encounter && state.activeEncounter) {
                const hex = get().selectedHex;
                if (hex) get().markEncounterCleared(hex.id || `HEX_${hex.index}`);
                set({ activeEncounter: null, selectedTargetId: null });
            }

            // Handle VTT Commands (like MOVE_TOKEN or START_COMBAT)
            if (update.vtt_commands) {
                update.vtt_commands.forEach((cmd: string) => {
                    console.log("[VTT] Received System Command:", cmd);
                });
            }

        } catch (err) {
            console.error(err);
            set({ ui_locked: false });
        }
    },

    executeAction: async (skillName: string, targetId: string) => {
        set({ ui_locked: true });
        try {
            const state = get();
            const activeEncounter = state.activeEncounter;
            const targetToken = activeEncounter?.tokens?.find((t: any) => t.id === targetId);

            // --- Real-time Skill Resolution ---
            // 1. Resolve Rank (Default to 0 if unknown)
            let skillRank = 0;
            if (state.characterSheet?.tactical_skills) {
                const skillData = state.characterSheet.tactical_skills[skillName];
                skillRank = typeof skillData === 'object' ? skillData.rank : (typeof skillData === 'number' ? skillData : 0);
            }

            // 2. Resolve Stat Mod (Lead Stat)
            // For now, we map common skills to their Sector I/II stats. 
            // In a full build, this is determined by the player's chosen "Lead" during creation.
            const skillToStatMap: Record<string, string> = {
                'Assault': 'might',
                'Ballistics': 'reflexes',
                'Fortify': 'fortitude',
                'Mobility': 'finesse',
                'Tactics': 'logic',
                'Deceive': 'charm',
                'Coercion': 'willpower',
                'Basic Attack': 'might',
                'Ranged Attack': 'reflexes'
            };
            const leadStat = skillToStatMap[skillName] || 'might';
            const statMod = state.attributes[leadStat] || 0;

            // 3. Tactical Advantage (Flanking / Engaged)
            const playerToken = activeEncounter.tokens.find(t => t.isPlayer);
            let hasAdvantage = false;
            let hasDisadvantage = false;

            if (playerToken && targetToken) {
                // Rule: Engaged if token has clashed this round
                const isEngaged = (targetToken.engaged_with?.length || 0) > 0;

                // Calculate Relative Position
                const dx = playerToken.x - targetToken.x;
                const dy = playerToken.y - targetToken.y;

                // Simplified Flanking: If target is engaged with someone else, side attacks get Advantage
                if (isEngaged && !targetToken.engaged_with?.includes(playerToken.id)) {
                    hasAdvantage = true;
                }

                // Sneak Attack: Attacking from behind (if orientation matches)
                // For now, if no direction, assume 'Front' is where the current engagement is.
            }

            const payload = {
                campaign_id: state.activeCampaignId,
                skill_name: skillName,
                skill_rank: skillRank,
                stat_mod: statMod,
                has_advantage: hasAdvantage,
                has_disadvantage: hasDisadvantage,
                target: {
                    id: targetId,
                    name: targetToken?.name || 'Unknown',
                    type: targetToken?.isPlayer ? 'Player' : 'Enemy'
                },
                attacker_attributes: state.attributes,
                attacker_vitals: state.vitals,
                equipped_items: state.clientLoadout
            };

            const res = await fetch('http://localhost:8000/api/player/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("API Gateway Action Delivery Failed.");

            const result = await res.json();

            // Track Engagement: Player and Target are now engaged
            set((s) => ({
                activeEncounter: s.activeEncounter ? {
                    ...s.activeEncounter,
                    tokens: s.activeEncounter.tokens.map(t => {
                        if (t.id === playerToken?.id) return { ...t, engaged_with: [...(t.engaged_with || []), targetId] };
                        if (t.id === targetId) return { ...t, engaged_with: [...(t.engaged_with || []), playerToken?.id || ''] };
                        return t;
                    })
                } : null
            }));

            get().addChatMessage({ sender: 'SYSTEM', text: `> ${skillName} vs ${targetToken?.name || 'Target'}: ${result.resolution_text || 'Action resolved.'}` });

            // 1. Delegate synchronization and victory logic
            if (result.vitals_update || result.new_target_hp !== undefined || result.encounter_ended) {
                get().syncCombatState({
                    ...result,
                    targetId: targetId
                });
            }

        } catch (e) {
            console.error(e);
            get().addChatMessage({ sender: 'ERROR', text: 'Action failed to reach Game Master.' });
        } finally {
            set({ ui_locked: false });
        }
    },

    syncCombatState: (result) => {
        const { new_target_hp, encounter_ended, vitals_update, targetId, clash_result } = result;

        // 1. Update NPC State (HP, Composure, etc.)
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

        // 2. Update Player Vitals (HP, Stamina, Focus, Composure)
        if (vitals_update) {
            get().setPlayerVitals(vitals_update);
        }

        // 3. Victory Protocol: Close tactical HUD if ended or HP 0
        const hex = get().selectedHex;
        if (encounter_ended || (new_target_hp !== undefined && new_target_hp <= 0)) {
            console.log("[VTT] Victory! Forcing tactical state clear.");
            if (hex) {
                get().markEncounterCleared(hex.id || `HEX_${hex.index || 'NULL'}`);
            }

            set({
                activeEncounter: null,
                selectedTargetId: null,
                ui_locked: false
            });

            get().addChatMessage({
                sender: 'SYSTEM',
                text: "CONQUEST: The enemy has been defeated. Combat resolved."
            });
        }
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
