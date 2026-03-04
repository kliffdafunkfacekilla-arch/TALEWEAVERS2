import { useState } from 'react';
import { PixiBattlemap } from './components/map/PixiBattlemap';
import { DirectorLog } from './components/left_panel/DirectorLog';
import { ActionDeck } from './components/bottom_console/ActionDeck';
import { ResourceOrbs } from './components/bottom_console/ResourceOrbs';
import { BioMatrix } from './components/right_panel/BioMatrix';
import { InventoryPanel } from './components/right_panel/InventoryPanel';
import { InjurySlots } from './components/right_panel/InjurySlots';
import { QuestTracker } from './components/hud/QuestTracker';
import { WorldArchitect } from './components/WorldArchitect';
import { CharacterSheet } from './components/CharacterSheet';
import { EncounterOverlay } from './components/hud/EncounterOverlay';
import { ActionHUD } from './components/hud/ActionHUD';
import { EvolutionUI } from './components/hud/EvolutionUI';
import { ExplorationNodeMap } from './components/map/ExplorationNodeMap';
import { MapRenderer } from './components/MapRenderer';
import { SurvivalScreen } from './components/survival/SurvivalScreen';
import { SettlementInspector } from './components/SettlementInspector';
import { useGameStore, type LoadoutItem, type VTTTier } from './store/useGameStore';
import { useCharacterStore } from './store/useCharacterStore';
import { useCombatStore } from './store/useCombatStore';
import './App.css';

export default function App() {
  const currentScreen = useGameStore((s) => s.currentScreen);
  const setScreen = useGameStore((s) => s.setScreen);
  const setCampaignId = useGameStore((s) => s.setCampaignId);
  const addChatMessage = useGameStore((s) => s.addChatMessage);
  const vttTier = useGameStore((s) => s.vttTier);
  const setVttTier = useGameStore((s) => s.setVttTier);
  const setClientLoadout = useGameStore((s) => s.setClientLoadout);

  const setCharacterSheet = useCharacterStore((s) => s.setCharacterSheet);
  const activeEncounter = useCombatStore((s) => s.activeEncounter);

  const [isBioMatrixOpen, setBioMatrixOpen] = useState(false);
  const [isEvolutionOpen, setEvolutionOpen] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  // ── THE REAL STARTUP SEQUENCE ──────────────────────────────────────
  const handleEnterCampaign = async () => {
    setIsStarting(true);
    try {
      const state = useGameStore.getState();

      if (!state.characterSheet) {
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
          equipped_loadout: { "main_hand": "wpn_rusted_cleaver", "consumable_1": "csm_ddust", "consumable_2": "csm_stamina_tea" },
          tactical_skills: {}
        };

        const charRes = await fetch(`${import.meta.env.VITE_SAGA_CHAR_ENGINE_URL || "http://localhost:8003"}/api/rules/character/calculate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildRequest)
        });

        if (charRes.ok) {
          const compiledSheet = await charRes.json();
          setCharacterSheet(compiledSheet);
        }
      }

      const STARTING_LOADOUT: LoadoutItem[] = [
        { id: 'wpn_steel_rapier', name: 'Steel Rapier', type: 'MELEE', target: 'ADJACENT', range: 1, stamina_cost: 1, dice: '1d8', desc: 'A swift, elegant thrust.' },
        { id: 'sk_snap_dodge', name: 'Snap Dodge', type: 'MOBILITY', target: 'SELF', range: 0, stamina_cost: 2, dice: 'None', desc: 'Evade an incoming blow.', lead_stat: 'reflexes', trail_stat: 'awareness', skill_rank: 2, target_dc: 15 },
        { id: 'csm_travelers_bread', name: 'Traveler\'s Bread', type: 'CONSUMABLE', target: 'SELF', range: 0, stamina_cost: 0, dice: '+STM', desc: 'Restores stamina.' },
      ];

      setClientLoadout(STARTING_LOADOUT);

      const campaignRes = await fetch(`${import.meta.env.VITE_SAGA_DIRECTOR_URL || "http://localhost:8000"}/api/campaign/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          world_id: 'W_001',
          starting_hex_id: 200500,
          player_id: 'PLAYER_001',
          player_sprite: useCharacterStore.getState().characterSheet?.avatar_sprite
        })
      });

      if (!campaignRes.ok) throw new Error("Saga Director API failed.");

      const campData = await campaignRes.json();
      setCampaignId(campData.campaign_id);

      await useGameStore.getState().sendAction("TRAVEL", 0, "200500");

      addChatMessage({
        sender: 'AI_DIRECTOR',
        text: 'The horizon stretches wide across the 1000x400 expanse of the globe. You stand in Hex #200500. What do you do?'
      });

      setScreen('PLAYER');
      setVttTier(2); // Start at Regional Travel

    } catch (err) {
      console.error(err);
      alert("Failed to reach Saga Director Engine. Is your server running?");
    } finally {
      setIsStarting(false);
    }
  };

  const renderVttContent = () => {
    // Priority: Tactical Combat takes precedence if activeEncounter exists
    if (activeEncounter || vttTier === 5) return <PixiBattlemap />;

    switch (vttTier) {
      case 1:
      case 2:
        return <MapRenderer />;
      case 3:
        return <SurvivalScreen />;
      case 4:
        return <ExplorationNodeMap />;
      default:
        return <MapRenderer />;
    }
  };

  // ─── MAIN MENU ─────────────────────────────────────────────────────
  if (currentScreen === 'MAIN_MENU') {
    return (
      <div className="w-screen h-screen bg-black flex flex-col items-center justify-center text-white overflow-hidden">
        <h1 className="text-5xl font-bold tracking-widest mb-12 text-transparent bg-clip-text bg-gradient-to-b from-white to-zinc-600 uppercase">
          T.A.L.E.W.E.A.V.E.R.
        </h1>
        <div className="flex flex-col gap-4">
          <button onClick={() => setScreen('WORLD_BUILDER')} className="w-72 px-6 py-4 border border-zinc-700 text-zinc-300 hover:border-amber-500 hover:text-amber-500 uppercase tracking-widest transition-all text-sm font-bold">Access God Engine</button>
          <button onClick={() => setScreen('CHARACTER_BUILDER')} className="w-72 px-6 py-4 border border-zinc-700 text-yellow-500 hover:border-yellow-500 hover:bg-yellow-900/10 uppercase tracking-widest transition-all text-sm font-bold">Soulweave Origin</button>
          <button onClick={handleEnterCampaign} disabled={isStarting} className="w-72 px-6 py-4 border border-red-700 bg-red-900/20 text-red-400 hover:bg-red-900/50 hover:text-red-300 uppercase tracking-widest transition-all font-bold shadow-[0_0_15px_rgba(220,38,38,0.2)] text-sm disabled:opacity-50">{isStarting ? 'Initializing...' : 'Enter Campaign'}</button>
        </div>
      </div>
    );
  }

  // ─── WORLD BUILDER ──────────────────────────────────────────────────
  if (currentScreen === 'WORLD_BUILDER') return <WorldArchitect onBack={() => setScreen('MAIN_MENU')} />;

  // ─── CHARACTER BUILDER ──────────────────────────────────────────────
  if (currentScreen === 'CHARACTER_BUILDER') return <div className="relative w-screen h-screen"><CharacterSheet /><button onClick={() => setScreen('MAIN_MENU')} className="absolute top-4 left-4 z-50 bg-black/50 border border-zinc-700 px-4 py-2 text-xs font-bold uppercase text-zinc-400 hover:text-white transition-all">← Exit Weaving</button></div>;

  // ─── GAMEPLAY: 5-Panel VTT Interface ────────────────────────────────
  return (
    <div className="fixed inset-0 overflow-hidden bg-zinc-950 text-white flex flex-col font-sans select-none">
      <div className="flex-grow flex relative min-h-0">
        {/* LEFT: Director's Log */}
        <div className="w-80 xl:w-96 bg-zinc-900/90 border-r border-zinc-800 flex flex-col z-10 flex-shrink-0">
          <DirectorLog />
        </div>

        {/* CENTER: The Main VTT Display (Tiered) */}
        <div className="flex-grow relative bg-black min-w-0">
          {renderVttContent()}
          <EncounterOverlay />
          <ActionHUD />
          <SettlementInspector />
          {isEvolutionOpen && <EvolutionUI onClose={() => setEvolutionOpen(false)} />}

          {/* Tier Breadcrumb / Zoom Control (Dev) */}
          <div className="absolute top-4 left-4 z-50 flex gap-2">
            {[1, 2, 3, 4, 5].map((t) => (
              <button
                key={t}
                onClick={() => setVttTier(t as VTTTier)}
                className={`w-8 h-8 flex items-center justify-center rounded-full border text-[10px] font-bold transition-all ${vttTier === t ? 'bg-amber-500 border-amber-400 text-black' : 'bg-black/50 border-zinc-700 text-zinc-500 hover:text-white'
                  }`}
              >
                T{t}
              </button>
            ))}
          </div>

          <div className="absolute top-4 right-4 z-20 pointer-events-none">
            <QuestTracker />
          </div>
        </div>

        {/* RIGHT DRAWER: Bio-Matrix */}
        <div className={`bg-zinc-900/95 border-l border-zinc-800 z-30 overflow-y-auto flex-shrink-0 transition-all duration-300 ease-in-out ${isBioMatrixOpen ? 'w-80 p-4 opacity-100' : 'w-0 p-0 opacity-0 overflow-hidden'}`}>
          {isBioMatrixOpen && (
            <div className="space-y-8">
              <BioMatrix />
              <InventoryPanel />
              <InjurySlots />
            </div>
          )}
        </div>

        {/* Toggle Drawer */}
        <button
          className={`absolute top-4 z-40 bg-zinc-800/90 px-3 py-1.5 rounded text-xs font-bold uppercase border border-zinc-700 transition-all ${isBioMatrixOpen ? 'right-84' : 'right-4'}`}
          onClick={() => setBioMatrixOpen(!isBioMatrixOpen)}
        >
          {isBioMatrixOpen ? '✕' : 'Matrix'}
        </button>

        <button
          className="absolute top-14 right-4 z-40 bg-zinc-800/90 px-3 py-1.5 rounded text-xs font-bold uppercase border border-amber-900/50 text-amber-500 hover:bg-amber-900/20 transition-all"
          onClick={() => setEvolutionOpen(true)}
        >
          Evolve
        </button>

        {/* Navigation */}
        <button className="absolute top-4 left-[calc(24rem+6rem)] z-40 bg-zinc-800/80 px-3 py-1.5 rounded text-xs font-bold uppercase transition-all" onClick={() => setScreen('MAIN_MENU')}>← Exit</button>
      </div>

      {/* BOTTOM SECTION: Action Console */}
      <div className="h-52 bg-zinc-950 border-t border-zinc-800 z-20 flex justify-center items-center shadow-[0_-10px_40px_rgba(0,0,0,0.5)] flex-shrink-0">
        <div className="flex items-end gap-6 w-full max-w-7xl px-6 h-full">
          <div className="flex items-end pb-4 flex-shrink-0"><ResourceOrbs /></div>
          <div className="flex-grow h-full"><ActionDeck /></div>
        </div>
      </div>
    </div>
  );
}
