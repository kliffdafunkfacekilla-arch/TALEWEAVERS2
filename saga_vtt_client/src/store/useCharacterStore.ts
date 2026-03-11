import { create } from 'zustand';

export interface ResourcePool {
    current: number;
    max: number;
}

export interface CoreAttributes {
    might: number; endurance: number; vitality: number; fortitude: number; reflexes: number; finesse: number;
    knowledge: number; logic: number; charm: number; willpower: number; awareness: number; intuition: number;
    [key: string]: number;
}

export interface Injuries {
    body: string[];
    mind: string[];
}

export interface PipBank {
    stars: number;
    scars: number;
    survivors: number;
}

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
    pip_bank?: PipBank;
    avatar_sprite?: {
        sheet_url: string;
        x: number;
        y: number;
        w: number;
        h: number;
    };
    composite_sprite?: any;
}

interface CharacterState {
    characterSheet: CharacterSheet | null;
    characterName: string;
    vitals: {
        hp: ResourcePool;
        stamina: ResourcePool;
        focus: ResourcePool;
        composure: ResourcePool;
    };
    attributes: CoreAttributes;
    injuries: Injuries;
    skills: string[];
    pip_bank: PipBank;

    setCharacterSheet: (sheet: CharacterSheet) => void;
    setPlayerVitals: (apiVitals: Record<string, number>) => void;
    addInjury: (track: 'body' | 'mind', injuryName: string) => void;
    updatePipBank: (pips: Partial<PipBank>) => void;
    evolveAttribute: (stat: string) => Promise<void>;
    evolveSkill: (skill: string) => Promise<void>;
}

export const useCharacterStore = create<CharacterState>((set, get) => ({
    characterSheet: null,
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
    skills: ['Assault', 'Coercion', 'Mobility', 'Precise Shot', 'Endure', 'Deceive'],
    pip_bank: { stars: 0, scars: 0, survivors: 0 },

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
        } : get().vitals,
        pip_bank: sheet.pip_bank || { stars: 0, scars: 0, survivors: 0 }
    }),

    setPlayerVitals: (apiVitals) => set((state) => {
        const getV = (pool: 'hp' | 'stamina' | 'focus' | 'composure') => {
            const flat = (apiVitals as any)[`current_${pool}`];
            const nested = (apiVitals as any)[pool]?.current;
            const direct = (apiVitals as any)[pool];
            return flat ?? nested ?? (typeof direct === 'number' ? direct : state.vitals[pool].current);
        };
        const getM = (pool: 'hp' | 'stamina' | 'focus' | 'composure') => {
            const flat = (apiVitals as any)[`max_${pool}`];
            const nested = (apiVitals as any)[pool]?.max;
            return flat ?? nested ?? state.vitals[pool].max;
        };
        return {
            vitals: {
                hp: { current: getV('hp'), max: getM('hp') },
                stamina: { current: getV('stamina'), max: getM('stamina') },
                focus: { current: getV('focus'), max: getM('focus') },
                composure: { current: getV('composure'), max: getM('composure') },
            }
        };
    }),

    addInjury: (track, injuryName) => set((state) => {
        if (state.injuries[track].length >= 4) return state;
        return {
            injuries: {
                ...state.injuries,
                [track]: [...state.injuries[track], injuryName]
            }
        };
    }),

    updatePipBank: (pips) => set((state) => ({
        pip_bank: { ...state.pip_bank, ...pips }
    })),

    evolveAttribute: async (stat) => {
        const state = get();
        if (!state.characterSheet) return;
        const res = await fetch(`${import.meta.env.VITE_SAGA_CHAR_ENGINE_URL || "http://localhost:8014"}/api/rules/character/evolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sheet: { ...state.characterSheet, attributes: state.attributes, pip_bank: state.pip_bank },
                expenditure: { type: 'STAR', target: stat }
            })
        });
        if (res.ok) state.setCharacterSheet(await res.json());
    },

    evolveSkill: async (skill) => {
        const state = get();
        if (!state.characterSheet) return;
        const res = await fetch(`${import.meta.env.VITE_SAGA_RULES_ENGINE_URL || "http://localhost:8014"}/api/rules/character/evolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sheet: { ...state.characterSheet, attributes: state.attributes, pip_bank: state.pip_bank },
                expenditure: { type: 'SCAR', target: skill }
            })
        });
        if (res.ok) state.setCharacterSheet(await res.json());
    }
}));
