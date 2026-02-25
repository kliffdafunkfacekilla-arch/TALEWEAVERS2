import { useState } from 'react';
import { PixiBattlemap } from './components/map/PixiBattlemap';
import { DirectorLog } from './components/left_panel/DirectorLog';
import { ActionDeck } from './components/bottom_console/ActionDeck';
import { ResourceOrbs } from './components/bottom_console/ResourceOrbs';
import { BioMatrix } from './components/right_panel/BioMatrix';
import { InjurySlots } from './components/right_panel/InjurySlots';
import { QuestTracker } from './components/hud/QuestTracker';
import { WorldArchitect } from './components/WorldArchitect';
import { useGameStore } from './store/useGameStore';
import type { LoadoutItem } from './store/useGameStore';
import './App.css';

export default function App() {
  const currentScreen = useGameStore((s) => s.currentScreen);
  const setScreen = useGameStore((s) => s.setScreen);
  const setCampaignId = useGameStore((s) => s.setCampaignId);
  const addChatMessage = useGameStore((s) => s.addChatMessage);
  const setPlayerVitals = useGameStore((s) => s.setPlayerVitals);
  const setCharacterSheet = useGameStore((s) => s.setCharacterSheet);
  const setClientLoadout = useGameStore((s) => s.setClientLoadout);
  const [isBioMatrixOpen, setBioMatrixOpen] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  // ── THE REAL STARTUP SEQUENCE ──────────────────────────────────────
  const handleEnterCampaign = async () => {
    setIsStarting(true);
    try {
      // ── STEP 1: Build Character via Port 8003 ──
      console.log("[VTT] Requesting True Character Sheet from Port 8003...");

      // Starting equipment + skills. Item IDs must exist in data/Item_Builder.json
      const STARTING_LOADOUT: LoadoutItem[] = [
        { id: 'wpn_rusted_cleaver', name: 'Rusted Cleaver', type: 'MELEE', target: 'ADJACENT', range: 1, stamina_cost: 1, dice: '1d8', desc: 'A heavy, brutal swing.' },
        { id: 'sk_snap_dodge', name: 'Snap Dodge', type: 'MOBILITY', target: 'SELF', range: 0, stamina_cost: 2, dice: 'None', desc: 'Evade an incoming blow. (Reflexes + Awareness)', lead_stat: 'reflexes', trail_stat: 'awareness', skill_rank: 2, target_dc: 15 },
        { id: 'sk_intimidate', name: 'Intimidate', type: 'SOCIAL', target: 'RANGED', range: 3, stamina_cost: 1, dice: 'None', desc: 'Break their composure. (Might + Charm)', lead_stat: 'might', trail_stat: 'charm', skill_rank: 1, target_dc: 12 },
        { id: 'csm_ddust', name: 'D-Dust Stim', type: 'CONSUMABLE', target: 'SELF', range: 0, stamina_cost: 0, dice: '+HP', desc: 'A raw injection of healing dust. Unstable.' },
        { id: 'csm_stamina_tea', name: 'Iron Root Tea', type: 'CONSUMABLE', target: 'SELF', range: 0, stamina_cost: 0, dice: '+STM', desc: 'Bitter tea that restores endurance.' },
      ];

      const buildRequest = {
        name: "Scavenger_01",
        base_attributes: {
          might: 3, endurance: 4, vitality: 5, fortitude: 3, reflexes: 4, finesse: 2,
          knowledge: 2, logic: 2, charm: 1, willpower: 3, awareness: 4, intuition: 3
        },
        evolutions: {
          species_base: "HUMAN",
          head_slot: "Standard", body_slot: "Standard", arms_slot: "Standard",
          legs_slot: "Standard", skin_slot: "Standard", special_slot: "None"
        },
        selected_powers: [],
        equipped_loadout: { "main_hand": "wpn_rusted_cleaver", "consumable_1": "csm_ddust", "consumable_2": "csm_stamina_tea" }
      };

      const charRes = await fetch('http://localhost:8003/api/rules/character/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildRequest)
      });

      if (!charRes.ok) {
        console.warn("[VTT] Character Engine offline. Using fallback vitals.");
        setPlayerVitals({ current_hp: 20, max_hp: 20, current_stamina: 12, max_stamina: 12, current_focus: 9, max_focus: 9, current_composure: 14, max_composure: 14 });
      } else {
        const compiledSheet = await charRes.json();
        console.log("[VTT] Character Sheet compiled:", compiledSheet.name);
        setCharacterSheet(compiledSheet);
        setPlayerVitals({
          current_hp: compiledSheet.vitals.max_hp,
          max_hp: compiledSheet.vitals.max_hp,
          current_stamina: compiledSheet.vitals.max_stamina,
          max_stamina: compiledSheet.vitals.max_stamina,
          current_focus: compiledSheet.vitals.max_focus,
          max_focus: compiledSheet.vitals.max_focus,
          current_composure: compiledSheet.vitals.max_composure,
          max_composure: compiledSheet.vitals.max_composure,
        });
      }

      // ── STEP 2: Set the client-side loadout for the Action Deck ──
      setClientLoadout(STARTING_LOADOUT);
      console.log("[VTT] Loadout equipped:", STARTING_LOADOUT.map(i => i.name).join(', '));

      // ── STEP 3: Start Campaign via Port 8000 ──
      console.log("[VTT] Connecting to Game Master on Port 8000...");
      const campaignRes = await fetch('http://localhost:8000/api/campaign/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          world_id: 'W_001',
          starting_hex_id: 402,
          player_id: 'PLAYER_001'
        })
      });

      if (!campaignRes.ok) throw new Error("Game Master API failed.");

      const campData = await campaignRes.json();
      setCampaignId(campData.campaign_id);
      console.log(`[VTT] Campaign ${campData.campaign_id} initialized.`);

      // ── STEP 4: AI Director introduction ──
      addChatMessage({
        sender: 'AI_DIRECTOR',
        text: 'The biting cold of the Deep Tundra pierces your armor. You stand in Hex #402. What do you do?'
      });

      // ── STEP 5: Transition to gameplay ──
      setScreen('PLAYER');

    } catch (err) {
      console.error(err);
      alert("Failed to reach Game Master Engine on Port 8000. Is your Python server running?");
    } finally {
      setIsStarting(false);
    }
  };

  // ─── MAIN MENU ─────────────────────────────────────────────────────
  if (currentScreen === 'MAIN_MENU') {
    return (
      <div className="w-screen h-screen bg-black flex flex-col items-center justify-center text-white overflow-hidden">
        <h1 className="text-5xl font-bold tracking-widest mb-12 text-transparent bg-clip-text bg-gradient-to-b from-white to-zinc-600">
          S.A.G.A. ENGINE
        </h1>

        <div className="flex flex-col gap-4">
          <button
            onClick={() => setScreen('WORLD_BUILDER')}
            className="w-72 px-6 py-4 border border-zinc-700 text-zinc-300 hover:border-amber-500 hover:text-amber-500 uppercase tracking-widest transition-all text-sm font-bold"
          >
            Access God Engine
          </button>

          <button
            onClick={handleEnterCampaign}
            disabled={isStarting}
            className="w-72 px-6 py-4 border border-red-700 bg-red-900/20 text-red-400 hover:bg-red-900/50 hover:text-red-300 uppercase tracking-widest transition-all font-bold shadow-[0_0_15px_rgba(220,38,38,0.2)] text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStarting ? 'Initializing...' : 'Enter Campaign'}
          </button>
        </div>

        <p className="mt-12 text-[10px] text-zinc-600 uppercase tracking-widest font-mono">
          T.A.L.E.W.E.A.V.E.R. Virtual Tabletop v0.1
        </p>
      </div>
    );
  }

  // ─── WORLD BUILDER ──────────────────────────────────────────────────
  if (currentScreen === 'WORLD_BUILDER') {
    return <WorldArchitect onBack={() => setScreen('MAIN_MENU')} />;
  }

  // ─── GAMEPLAY: 5-Panel VTT Interface ────────────────────────────────
  return (
    <div className="w-screen h-screen overflow-hidden bg-zinc-950 text-white flex flex-col font-sans select-none">

      {/* ═══ TOP / MIDDLE SECTION ═══ */}
      <div className="flex-grow flex relative min-h-0">

        {/* LEFT: Director's Log */}
        <div className="w-80 xl:w-96 bg-zinc-900/90 border-r border-zinc-800 flex flex-col z-10 flex-shrink-0">
          <DirectorLog />
        </div>

        {/* CENTER: The Map */}
        <div className="flex-grow relative bg-black min-w-0">
          <PixiBattlemap />

          {/* FLOATING TOP-RIGHT: Quest Tracker HUD */}
          <div className="absolute top-4 right-4 z-20 pointer-events-none">
            <QuestTracker />
          </div>
        </div>

        {/* RIGHT DRAWER: Bio-Matrix */}
        <div className={`
          bg-zinc-900/95 border-l border-zinc-800 shadow-2xl z-30
          overflow-y-auto flex-shrink-0 transition-all duration-300 ease-in-out
          ${isBioMatrixOpen ? 'w-72 xl:w-80 p-4 opacity-100' : 'w-0 p-0 opacity-0 overflow-hidden'}
        `}>
          <div className={`${isBioMatrixOpen ? '' : 'invisible'}`}>
            <BioMatrix />
            <InjurySlots />
          </div>
        </div>

        {/* Toggle Drawer Button */}
        <button
          className={`
            absolute top-3 z-40 bg-zinc-800/90 backdrop-blur-sm
            px-3 py-1.5 rounded-lg hover:bg-zinc-700
            text-xs font-bold uppercase tracking-wider text-zinc-400 hover:text-zinc-200
            transition-all duration-200 border border-zinc-700/50
            ${isBioMatrixOpen ? 'right-[calc(18rem+1rem)] xl:right-[calc(20rem+1rem)]' : 'right-4'}
          `}
          style={{ transition: 'right 300ms ease-in-out, background-color 200ms, color 200ms' }}
          onClick={() => setBioMatrixOpen(!isBioMatrixOpen)}
        >
          {isBioMatrixOpen ? '✕ Close' : '☰ Matrix'}
        </button>

        {/* Navigation Buttons */}
        <button
          className="absolute top-3 left-[calc(20rem+1rem)] xl:left-[calc(24rem+1rem)] z-40 bg-amber-800/80 backdrop-blur-sm px-3 py-1.5 rounded-lg hover:bg-amber-700 text-xs font-bold uppercase tracking-wider text-amber-200 hover:text-white transition-all duration-200 border border-amber-700/50"
          onClick={() => setScreen('WORLD_BUILDER')}
        >
          ⚙ Architect
        </button>

        <button
          className="absolute top-12 left-[calc(20rem+1rem)] xl:left-[calc(24rem+1rem)] z-40 bg-zinc-800/80 backdrop-blur-sm px-3 py-1.5 rounded-lg hover:bg-zinc-700 text-xs font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-all duration-200 border border-zinc-700/50"
          onClick={() => setScreen('MAIN_MENU')}
        >
          ← Menu
        </button>
      </div>

      {/* ═══ BOTTOM SECTION: Action Console ═══ */}
      <div className="h-52 bg-zinc-950 border-t border-zinc-800 z-20 flex justify-center items-center shadow-[0_-10px_40px_rgba(0,0,0,0.5)] flex-shrink-0">
        <div className="flex items-end gap-6 w-full max-w-7xl px-6 h-full">
          {/* Resource Orbs */}
          <div className="flex items-end pb-4 flex-shrink-0">
            <ResourceOrbs />
          </div>

          {/* Action Deck */}
          <div className="flex-grow h-full">
            <ActionDeck />
          </div>
        </div>
      </div>
    </div>
  );
}
