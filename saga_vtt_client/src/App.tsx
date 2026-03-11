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
import { SoulweaveWizard } from './components/SoulweaveWizard';
import { EncounterOverlay } from './components/hud/EncounterOverlay';
import { ActionHUD } from './components/hud/ActionHUD';
import { EvolutionUI } from './components/hud/EvolutionUI';
import { ExplorationNodeMap } from './components/map/ExplorationNodeMap';
import { MapRenderer } from './components/MapRenderer';
import { SurvivalScreen } from './components/survival/SurvivalScreen';
import { SettlementInspector } from './components/SettlementInspector';
import { useGameStore, type VTTTier } from './store/useGameStore';
import { useCharacterStore } from './store/useCharacterStore';
import { useCombatStore } from './store/useCombatStore';
import { generateLoadoutFromSheet } from './utils/loadoutMapper';
import { CampaignSetup } from './components/CampaignSetup';
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
  const [isIngesting, setIsIngesting] = useState(false);
  const [isImportingMap, setIsImportingMap] = useState(false);
  const [mapFilename, setMapFilename] = useState("my_map.map");

  // ── THE REAL STARTUP SEQUENCE ──────────────────────────────────────
  const handleEnterCampaign = async (settings: any) => {
    setIsStarting(true);
    try {
      const state = useGameStore.getState();
      let finalSheet = state.characterSheet;

      // ── STEP 1: Build default character if none exists ──────────────────
      if (!finalSheet) {
        try {
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
          const charRes = await fetch(`${import.meta.env.VITE_SAGA_CHAR_ENGINE_URL || "http://localhost:8014"}/api/rules/character/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildRequest)
          });
          if (charRes.ok) {
            finalSheet = await charRes.json();
            setCharacterSheet(finalSheet);
          } else {
            console.warn(`[LAUNCH] Character Engine returned ${charRes.status} — using defaults.`);
          }
        } catch (charErr) {
          console.warn("[LAUNCH] Character Engine unreachable — using defaults.", charErr);
        }
      }

      if (finalSheet) {
        const dynamicLoadout = generateLoadoutFromSheet(finalSheet);
        setClientLoadout(dynamicLoadout);
      }

      // ── STEP 2: Start the campaign ──────────────────────────────────────
      const directorUrl = import.meta.env.VITE_SAGA_DIRECTOR_URL || "http://localhost:8050";
      let campaignRes: Response;
      try {
        campaignRes = await fetch(`${directorUrl}/api/campaign/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            world_id: 'W_001',
            starting_hex_id: 200500,
            player_id: 'PLAYER_001',
            composite_sprite: useCharacterStore.getState().characterSheet?.composite_sprite ?? null,
            ...settings
          })
        });
      } catch (networkErr: any) {
        throw new Error(`[LAUNCH] Cannot reach Director at ${directorUrl}. Is saga_director running? (${networkErr.message})`);
      }

      if (!campaignRes.ok) {
        let detail = '';
        try { detail = JSON.stringify(await campaignRes.json()); } catch { }
        throw new Error(`[LAUNCH] Director returned ${campaignRes.status}: ${detail}`);
      }

      // ── STEP 3: Parse and sync state ────────────────────────────────────
      let campData: any;
      try {
        campData = await campaignRes.json();
      } catch (parseErr: any) {
        throw new Error(`[LAUNCH] Director response could not be parsed: ${parseErr.message}`);
      }

      setCampaignId(campData.campaign_id);

      // ── STEP 4: Normalize and sync state ──────────────────────────────
      // The Director response may have `initial_state` as a nested object
      const initial = campData.initial_state ?? campData;

      // 4a. Normalize active_encounter — add required `data` field if missing
      const rawEncounter = initial.active_encounter ?? campData.active_encounter;
      if (rawEncounter) {
        const encounter = {
          ...rawEncounter,
          gridWidth: rawEncounter.gridWidth ?? (rawEncounter.grid && rawEncounter.grid.length > 0 ? rawEncounter.grid[0].length : 15),
          gridHeight: rawEncounter.gridHeight ?? (rawEncounter.grid ? rawEncounter.grid.length : 10),
          // EncounterOverlay requires a `data` object with `category`. Provide defaults.
          data: rawEncounter.data ?? {
            category: rawEncounter.metadata?.biome ?? 'AMBIENT',
            title: rawEncounter.encounter_id ?? 'Arrival',
            narrative_prompt: initial.narration ?? 'You have arrived.',
            npcs: [],
            enemies: [],
          },
          // Tokens require current_hp / max_hp
          tokens: (rawEncounter.tokens ?? []).map((t: any) => ({
            current_hp: t.hp ?? 10,
            max_hp: t.hp ?? 10,
            ...t,
          })),
          interactionHistory: rawEncounter.interactionHistory ?? [],
        };
        useCombatStore.getState().setActiveEncounter(encounter);
      }

      // 4b. World state — chaos_numbers may be a single int or an array
      if (initial.weather) useGameStore.setState({ weather: initial.weather });
      if (initial.tension !== undefined) useGameStore.setState({ tension: initial.tension });
      const rawChaos = initial.chaos_numbers;
      if (rawChaos !== undefined) {
        useGameStore.setState({ chaosNumbers: Array.isArray(rawChaos) ? rawChaos : [rawChaos] });
      }
      if (initial.pacing) useGameStore.setState({ pacingProgress: initial.pacing });

      // 4c. Narration
      const narrationText = campData.narration || initial.narration || initial.ai_narration || "You have arrived. The journey begins.";
      addChatMessage({ sender: 'AI_DIRECTOR', text: narrationText });


      setScreen('PLAYER');
      setVttTier(5);

    } catch (err: any) {
      console.error("[LAUNCH FAILURE]", err);
      alert(`Campaign launch failed:\n\n${err.message || err}\n\nCheck browser console (F12) for details.`);
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
          <div className="h-px bg-zinc-800 w-full my-2" />
          <button
            onClick={() => handleEnterCampaign({})}
            disabled={isStarting}
            className="w-72 px-6 py-4 bg-white text-black hover:bg-yellow-500 uppercase tracking-[0.2em] transition-all font-black shadow-[0_0_20px_rgba(255,255,255,0.2)] text-sm disabled:opacity-50"
          >
            {isStarting ? 'MATERIALIZING...' : 'QUICK START (SKIP TO VTT)'}
          </button>
          <button onClick={() => setScreen('CAMPAIGN_SETUP')} disabled={isStarting} className="w-72 px-6 py-4 border border-red-700 bg-red-900/20 text-red-400 hover:bg-red-900/50 hover:text-red-300 uppercase tracking-widest transition-all font-bold text-sm disabled:opacity-50">Custom Campaign</button>
          <button onClick={() => setScreen('OPTIONS')} className="w-72 px-4 py-2 border border-zinc-800 text-zinc-600 hover:text-zinc-400 uppercase tracking-widest transition-all text-[10px]">System Options</button>
        </div>
      </div>
    );
  }

  // ─── OPTIONS MENU ───────────────────────────────────────────────────
  if (currentScreen === 'OPTIONS') {
    const handleIngestion = async () => {
      setIsIngesting(true);
      try {
        const architectUrl = import.meta.env.VITE_SAGA_ARCHITECT_URL || 'http://localhost:8013';
        const res = await fetch(`${architectUrl}/api/lore/generate_entities`, { method: "POST" });
        if (res.ok) {
          alert("Lore Engine Activated! Entity generation is running in the background terminal.");
        } else {
          alert("Error: Could not reach Architect Module.");
        }
      } catch (e) {
        alert("Failed to connect to Lore Vault API.");
      } finally {
        setIsIngesting(false);
      }
    };

    const handleMapImport = async () => {
      if (!mapFilename) return;
      setIsImportingMap(true);
      try {
        const architectUrl = import.meta.env.VITE_SAGA_ARCHITECT_URL || 'http://localhost:8013';
        const res = await fetch(`${architectUrl}/api/lore/import_map`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: mapFilename })
        });
        if (res.ok) {
          alert(`Map Import Activated for ${mapFilename}! Check background terminal for progress.`);
        } else {
          alert("Error: Could not reach Lore Module.");
        }
      } catch (e) {
        alert("Failed to connect to backend API.");
      } finally {
        setIsImportingMap(false);
      }
    };

    return (
      <div className="w-screen h-screen bg-black flex flex-col items-center justify-center text-white overflow-hidden">
        <h2 className="text-4xl font-bold tracking-widest mb-12 text-zinc-400 uppercase">
          System Options
        </h2>
        <div className="w-[600px] border border-zinc-800 p-8 flex flex-col gap-6 bg-zinc-950">
          <div>
            <h3 className="text-amber-500 font-bold uppercase mb-2">Automated Data Pipeline</h3>
            <p className="text-zinc-500 text-sm mb-4">
              Launches the backend LLM script. It scans `data/vault/entities/` for `.md` lore files and generates perfectly statted `.json` Game Engine entities automatically.
            </p>
            <button
              onClick={handleIngestion}
              disabled={isIngesting}
              className="w-full px-6 py-3 border border-amber-800 text-amber-500 hover:bg-amber-900/20 uppercase tracking-wider font-bold text-sm transition-all"
            >
              {isIngesting ? "Initializing Matrix..." : "Activate Lore Ingestion"}
            </button>
          </div>

          <div className="pt-4 border-t border-zinc-800">
            <h3 className="text-emerald-500 font-bold uppercase mb-2">Map File Importer</h3>
            <p className="text-zinc-500 text-sm mb-4">
              Imports custom image files (`.png`, `.jpg`) or Azgaar exports (`.map`) directly into the game engine's `Saga_Master_World.json` grid logic. Place your file in the `data/` folder, type the exact filename below, and execute.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={mapFilename}
                onChange={(e) => setMapFilename(e.target.value)}
                placeholder="e.g. azgaar_export.map"
                className="flex-grow bg-zinc-900 border border-zinc-700 px-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              />
              <button
                onClick={handleMapImport}
                disabled={isImportingMap || !mapFilename}
                className="px-6 py-2 border border-emerald-800 text-emerald-400 hover:bg-emerald-900/20 uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50"
              >
                {isImportingMap ? "Importing..." : "Execute Import"}
              </button>
            </div>
          </div>

          <button onClick={() => setScreen('MAIN_MENU')} className="mt-6 px-6 py-3 border border-zinc-700 text-zinc-400 hover:bg-zinc-800 uppercase tracking-widest text-sm font-bold">
            ← Return to Main Menu
          </button>
        </div>
      </div>
    );
  }

  // ─── CAMPAIGN CALIBRATION (SESSION ZERO) ────────────────────────────
  if (currentScreen === 'CAMPAIGN_SETUP') {
    return (
      <div className="relative w-screen h-screen">
        <CampaignSetup onCommence={handleEnterCampaign} />
        <button onClick={() => setScreen('MAIN_MENU')} className="absolute top-4 left-4 z-50 bg-black/50 border border-zinc-700 px-4 py-2 text-xs font-bold uppercase text-zinc-400 hover:text-white transition-all">← Cancel Setup</button>
      </div>
    );
  }

  // ─── WORLD BUILDER ──────────────────────────────────────────────────
  if (currentScreen === 'WORLD_BUILDER') return <WorldArchitect onBack={() => setScreen('MAIN_MENU')} />;

  // ─── CHARACTER BUILDER ──────────────────────────────────────────────
  if (currentScreen === 'CHARACTER_BUILDER') return <SoulweaveWizard />;

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
