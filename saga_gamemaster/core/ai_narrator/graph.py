from langgraph.graph import StateGraph, END
from core.ai_narrator.state import GameState
from core.api_gateway import SAGA_API_Gateway
import asyncio
import json
import logging
import random

api_gateway = SAGA_API_Gateway()

try:
    from langchain_community.llms import Ollama
    local_llm = Ollama(model="llama3")
    OLLAMA_AVAILABLE = True
except ImportError:
    local_llm = None
    OLLAMA_AVAILABLE = False
except Exception as e:
    local_llm = None
    OLLAMA_AVAILABLE = False

async def fetch_context_node(state: GameState):
    campaign_data = await api_gateway.get_campaign_state(state["player_id"])
    vitals = state.get("player_vitals")
    if not vitals:
        char_data = await api_gateway.get_character(state["player_id"])
        vitals = char_data["survival_pools"]
    
    return {
        "current_location": campaign_data["current_node_name"],
        "active_quests": campaign_data["active_quests"],
        "player_vitals": vitals,
        "active_regional_arcs": state.get("active_regional_arcs") or [],
        "active_local_quests": state.get("active_local_quests") or [],
        "active_errands": state.get("active_errands") or []
    }

async def resolve_mechanics_node(state: GameState):
    action = state["action_type"]
    target = state["action_target"]
    
    if action == "USE_ITEM":
        result = await api_gateway.use_item(state["player_id"], target)
        return {"math_log": f"[SYSTEM: {result['item_name']} consumed. {result['effect']} applied.]"}
    
    elif action == "ATTACK":
        vitals = state.get("player_vitals", {})
        attacker_data = {
            "name": state["player_id"],
            "current_hp": vitals.get("current_hp", 20),
            "attack_or_defense_pool": vitals.get("stamina", 5) + state.get("stamina_burned", 0),
            "weapon_damage_dice": "1d8",
            "stamina_burned": state.get("stamina_burned", 0),
            "focus_burned": 0
        }
        defender_data = {
            "name": target, "current_hp": 15, "attack_or_defense_pool": 4, "weapon_damage_dice": "1d6", "stamina_burned": 0, "focus_burned": 0
        }
        result = await api_gateway.resolve_clash(attacker_data, defender_data)
        return {"math_log": f"[SYSTEM: Clash Result: {result['clash_result']}. Damage: {result['defender_hp_change']}.]"}
    
    elif action in ["MOVE", "TRAVEL"]:
        return {"math_log": f"[SYSTEM: Moving to {target}.]"}
    
    elif action == "SURVIVAL":
        vitals = state.get("player_vitals", {})
        text = state.get("raw_chat_text", "").lower()
        math_msg = ""
        if "fire" in text:
            vitals["stamina"] = min(vitals.get("max_stamina", 12), vitals.get("stamina", 0) + 2)
            math_msg = "Fire built. +2 Stamina."
        return {"math_log": f"[SYSTEM Survival: {math_msg}]", "player_vitals": vitals}

    return {"math_log": "[SYSTEM: Action requires no math.]"}

async def director_node(state: GameState):
    """Tiered Narrative Director: Pulls story detail based on zoom level."""
    if state["action_type"] not in ["MOVE", "TRAVEL"]:
        return {"director_override": None, "vtt_commands": [], "active_encounter": state.get("active_encounter")}
    
    current_hex = state["action_target"]
    is_regional_move = state["action_type"] == "TRAVEL" # Tier 2/3 Scale
    
    # 1. Check for Regional Arc Generation (Tier 2/3)
    # If moving between cities/regions and no arc is active, generate one.
    if is_regional_move and not state.get("active_regional_arcs"):
        print("[DIRECTOR] Generating Regional Arc (Tier 2)...")
        idx = state["current_stage"]
        saga_beat = state["campaign_framework"][idx] if state.get("campaign_framework") else {}
        new_arcs = await api_gateway.generate_regional_arc(saga_beat, {"location": current_hex})
        return {"active_regional_arcs": new_arcs}

    # 2. Check for Local Side Quest (Tier 4)
    # If exploring a hex (pacing phase) and chance hits, generate a sidequest.
    pacing_goal = 2
    if state.get("campaign_framework") and state["current_stage"] < len(state["campaign_framework"]):
         pacing_goal = state["campaign_framework"][state["current_stage"]].get("pacing_milestones", 2)

    if state["current_stage_progress"] < pacing_goal and random.random() < 0.3:
        print("[DIRECTOR] Generating Local Side Quest (Tier 3)...")
        side_quest = await api_gateway.generate_local_sidequest({"hex_id": current_hex})
        if side_quest:
            return {"active_local_quests": state.get("active_local_quests", []) + [side_quest]}

    # 3. Check for Tactical Errand (Tier 5)
    if random.random() < 0.1:
        print("[DIRECTOR] Triggering Tactical Errand (Tier 4)...")
        errand = await api_gateway.generate_tactical_errand(str(current_hex))
        if errand:
            return {"active_errands": state.get("active_errands", []) + [errand]}

    # 4. Standard Encounters (Fallthrough)
    trigger = await api_gateway.check_quest_triggers(current_hex)
    encounter_request = {
        "biome": state.get("current_location", "Wilderness"),
        "threat_level": 2,
        "faction_territory": "The Wolf Cult" if trigger else "Wilderness"
    }

    encounter = None
    if trigger:
        encounter_request.update({"forced_type": trigger["type"], "seed_prompt": trigger.get("seed")})
        encounter = await api_gateway.generate_encounter(encounter_request)
    else:
        # Pacing awareness for random filler encounters
        base_chance = 0.15
        if state.get("current_stage_progress", 0) < pacing_goal:
            base_chance = 0.40
            print(f"[DIRECTOR] Pacing Mode: Chance raised to {base_chance}")

        if random.random() < base_chance:
            encounter = await api_gateway.generate_encounter(encounter_request)

    if encounter:
        tokens = [{"id": "PLAYER_001", "name": state.get("player_id", "Player"), "isPlayer": True, "current_hp": state.get("player_vitals", {}).get("current_hp", 20)}]
        encounter["tokens"] = tokens
        return {
            "director_override": f"[DIRECTOR OVERRIDE: {encounter['data']['category']} ENCOUNTER] {encounter['data']['title']}",
            "vtt_commands": [f"START_ENCOUNTER:{encounter['encounter_id']}"],
            "active_encounter": encounter
        }
    
    return {"director_override": None, "vtt_commands": [], "active_encounter": None}

async def narrator_node(state: GameState):
    print("[GRAPH] Node: Generating Narration with Foresight...")
    
    history_str = ""
    if state.get("chat_history"):
        for msg in state["chat_history"][-5:]: # Last 5 for prompt efficiency
            role = "TRAVELER" if msg["role"] == "user" else "NARRATOR"
            history_str += f"{role}: {msg['content']}\n"
    
    foresight_context = ""
    if state.get("campaign_framework"):
        idx = state["current_stage"]
        saga = state["campaign_framework"][idx]
        pacing_goal = saga.get('pacing_milestones', 2)
        
        # Build Hierarchy View for LLM
        arcs = "\n- ".join([a['narrative_objective'] for a in state.get("active_regional_arcs", [])])
        local = "\n- ".join([l['narrative_objective'] for l in state.get("active_local_quests", [])])
        errands = "\n- ".join([e['narrative_objective'] for e in state.get("active_errands", [])])

        foresight_context = f"""
        --- SAGA STAGE: {saga['stage_name']} ---
        Global Goal: {saga['narrative_objective']}
        
        --- ACTIVE REGIONAL ARCS (Tier 2) ---
        - {arcs if arcs else "None"}
        
        --- LOCAL SIDE QUESTS (Tier 3) ---
        - {local if local else "None"}
        
        --- TACTICAL ERRANDS (Tier 4) ---
        - {errands if errands else "None"}

        [PACING]: {state['current_stage_progress']}/{pacing_goal} filler events completed.
        [FORESHADOWING]: {saga.get('foreshadowing_clue', 'None')}
        """

    prompt = f"""
    You are the GM of S.A.G.A. (Gritty/Brutal Tone).
    {history_str}
    Location: {state['current_location']}
    Vitals: {state['player_vitals']}
    {foresight_context}
    Result: {state['math_log']}
    """
    
    if state.get("director_override"):
        prompt += f"\n\n{state['director_override']}\nNarrate in 3 sentences."
    else:
        prompt += f"\n\nAction: '{state['raw_chat_text']}'\nNarrate outcome in 3 gritty sentences. Drop foreshadowing if atmospheric."

    if OLLAMA_AVAILABLE and local_llm:
        try:
            response = local_llm.invoke(prompt)
            narrative = response.strip()
        except: narrative = f"Silence... (Offline)"
    else:
        narrative = f"[AI]: {prompt}"
        
    return {"ai_narration": narrative}

async def check_narrative_shift_node(state: GameState):
    """Detects progression or radical shifts requiring framework adjustment."""
    current_text = state.get("ai_narration", "").lower()
    history = state.get("chat_history", [])
    current_stage_idx = state["current_stage"]
    current_progress = state["current_stage_progress"]
    
    framework = state.get("campaign_framework", [])
    pacing_goal = 2 # Default fallback
    if framework and current_stage_idx < len(framework):
        pacing_goal = framework[current_stage_idx].get("pacing_milestones", 2)

    # 1. Pacing Tracking: Detect "Filler/Side" content completion
    # If a micro-encounter or survival event happened, increment progress
    if state.get("active_encounter") is None and ("objective complete" in current_text or "survived" in current_text):
        current_progress += 1
        print(f"[DIRECTOR] Pacing progress: {current_progress}/{pacing_goal}")

    # 2. Main Plot Progression: Only allow if pacing goal met
    if any(k in current_text for k in ["new chapter", "journey begins", "path revealed"]):
        if current_progress >= pacing_goal:
            new_stage = min(len(framework) - 1, current_stage_idx + 1)
            print(f"[DIRECTOR] Pacing met. Advancing to Stage {new_stage}. Clearing old sub-arcs.")
            return {
                "current_stage": new_stage, 
                "current_stage_progress": 0,
                "active_regional_arcs": [],
                "active_local_quests": [],
                "active_errands": []
            }
        else:
            print(f"[DIRECTOR] Progression blocked. Pacing {current_progress}/{pacing_goal} required.")
            return {"current_stage_progress": current_progress}
        
    # 3. Radical Divergence Check (Patching)
    if "enemy defeated" in state.get("math_log", "").lower() and "traitor" in current_text:
        print("[DIRECTOR] Major Plot Conflict! Requesting Framework adjustment...")
        updated_framework = await api_gateway.generate_framework(
            characters=[{"name": state["player_id"]}],
            world_state={}, 
            settings={"difficulty": "STANDARD"},
            history=history[-10:]
        )
        if updated_framework:
             return {"campaign_framework": updated_framework["hero_journey"]}

    return {"current_stage": current_stage_idx, "current_stage_progress": current_progress}

def create_director_graph():
    workflow = StateGraph(GameState)
    workflow.add_node("fetch_context", fetch_context_node)
    workflow.add_node("resolve_mechanics", resolve_mechanics_node)
    workflow.add_node("director", director_node)
    workflow.add_node("narrator", narrator_node)
    workflow.add_node("narrative_shift", check_narrative_shift_node)
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", "resolve_mechanics")
    workflow.add_edge("resolve_mechanics", "director")
    workflow.add_edge("director", "narrator")
    workflow.add_edge("narrator", "narrative_shift")
    workflow.add_edge("narrative_shift", END)
    return workflow.compile()
