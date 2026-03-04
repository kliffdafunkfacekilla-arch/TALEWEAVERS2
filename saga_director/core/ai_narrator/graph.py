from langgraph.graph import StateGraph, END
from core.ai_narrator.state import GameState
from core.api_gateway import SAGA_API_Gateway
import asyncio
import json
import logging
import random

api_gateway = SAGA_API_Gateway()

try:
    from langchain_ollama import OllamaLLM
    local_llm = OllamaLLM(model="llama3")
    OLLAMA_AVAILABLE = True
except ImportError:
    # Fallback to older community import if langchain-ollama isn't installed yet
    try:
        from langchain_community.llms import Ollama
        local_llm = Ollama(model="llama3")
        OLLAMA_AVAILABLE = True
    except:
        local_llm = None
        OLLAMA_AVAILABLE = False
except Exception as e:
    local_llm = None
    OLLAMA_AVAILABLE = False

async def fetch_context_node(state: GameState):
    # Fetch hex details for biome/tension scaling
    hex_id = int(state.get("action_target", 0)) if state.get("action_type") in ["MOVE", "TRAVEL"] else int(state.get("current_location", 0))
    hex_details = await api_gateway.get_hex_details(hex_id)
    
    vitals = state.get("player_vitals")
    powers = state.get("player_powers")
    
    if not vitals or not powers:
        char_data = await api_gateway.get_character(state["player_id"])
        if char_data:
            vitals = vitals or char_data["survival_pools"]
            powers = powers or char_data.get("powers", [])
    
    # Simple Weather Logic
    weathers = ["Clear Skies", "Overcast", "Heavy Rain", "Freezing Winds", "Toxic Fog"]
    current_weather = state.get("weather") or random.choice(weathers)
    
    return {
        "current_location": str(hex_id),
        "player_vitals": vitals,
        "player_powers": powers,
        "weather": current_weather,
        "tension": state.get("tension", 0),
        "chaos_numbers": state.get("chaos_numbers", [random.randint(1, 12)]),
        "active_regional_arcs": state.get("active_regional_arcs") or [],
        "active_local_quests": state.get("active_local_quests") or [],
        "active_errands": state.get("active_errands") or []
    }

async def resolve_mechanics_node(state: GameState):
    action = state["action_type"]
    target = state["action_target"]
    text = state.get("raw_chat_text", "").lower()
    
    # TAG SYSTEM HOOK: Fetch area tags
    current_hex_id = int(state["current_location"] if state["current_location"].isdigit() else 0)
    hex_details = await api_gateway.get_hex_details(current_hex_id)
    area_tags = hex_details.get("tags", [])
    
    vitals = state.get("player_vitals", {})

    if action == "STUNT":
        # Rule Stretching & Improvisation
        stunt_log = "[STUNT] "
        cost_focus = 0
        cost_stamina = 0
        
        # 1. Rule Stretching: Extra Movement
        if "move" in text or "reach" in text:
            cost_focus = 2
            stunt_log += "Stretching limits to reach further. "
        
        # 2. Tag Interaction: Environmental Stunts
        found_tag = None
        for tag in area_tags:
            if tag in text:
                found_tag = tag
                break
        
        if found_tag:
            cost_stamina += 1
            stunt_log += f"Leveraging the {found_tag}. "
            if found_tag == "swingable":
                stunt_log += "Momentum burst! "
            elif found_tag == "cover":
                stunt_log += "Defensive edge gained. "
        else:
            # Improvised leverage if no tag matches but intent is there
            cost_focus += 1
            stunt_log += "Improvising with the environment. "

        if vitals.get("focus", 0) < cost_focus or vitals.get("stamina", 0) < cost_stamina:
            return {"math_log": f"[SYSTEM: Stunt failed. Insufficient resources ({vitals.get('focus')}/{cost_focus} Focus, {vitals.get('stamina')}/{cost_stamina} Stamina).]"}
            
        vitals["focus"] -= cost_focus
        vitals["stamina"] -= cost_stamina
        
        return {
            "math_log": stunt_log + f"Success. (Cost: {cost_focus}F, {cost_stamina}S).",
            "player_vitals": vitals,
            "director_override": "[IMPROV SUCCESS] The traveler has turned the tide with a creative maneuver!"
        }
    
    if action == "USE_ITEM":
        result = await api_gateway.use_item(state["player_id"], target)
        return {"math_log": f"[SYSTEM: {result['item_name']} consumed. {result['effect']} applied.]"}
    
    elif action == "ATTACK":
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
    
    elif action == "SPELLCAST":
        powers = state.get("player_powers", [])
        spell_name = target
        
        power_data = next((p for p in powers if p["name"].lower() == spell_name.lower()), None)
        if not power_data:
            return {"math_log": f"[SYSTEM: Action failed. Spell '{spell_name}' not found.]"}
            
        cast_request = {
            "spell_name": spell_name,
            "school": power_data.get("school", "NEXUS"),
            "base_intensity": power_data.get("intensity", 1),
            "character_stats": {}, 
            "environment_context": {
                "biome": hex_details.get("biome", "Wilderness"),
                "weather": state.get("weather", "Clear Skies")
            },
            "dust_amount": 0, 
            "chaos_level": 1 
        }
        
        resolution = await api_gateway.resolve_spell(cast_request)
        
        math_msg = resolution["math_log"]
        if "dense_canopy" in area_tags and power_data.get("school") == "VITA":
             math_msg += " [TAG RESONANCE: Dense Canopy boosts Vita flow (+1 Intensity)]"
             resolution["final_intensity"] += 1
        
        cost = resolution["focus_cost"]
        current_focus = vitals.get("focus", 0)
        
        if current_focus < cost:
             return {"math_log": f"[SYSTEM: Action failed. Insufficient Focus ({current_focus}/{cost}).]"}
        
        vitals["focus"] -= cost
        
        return {
            "math_log": math_msg,
            "player_vitals": vitals,
            "chaos_narrative": resolution.get("volatility_narrative"),
            "director_override": resolution.get("resonance_narrative")
        }

    elif action == "SURVIVAL":
        math_msg = ""
        if "rest" in text or target == "REST":
            # REST MECHANIC: Recover pools but maybe spend resources
            vitals["stamina"] = min(vitals.get("max_stamina", 20), vitals.get("stamina", 0) + 5)
            vitals["hp"] = min(vitals.get("max_hp", 20), vitals.get("hp", 0) + 2)
            vitals["focus"] = min(vitals.get("max_focus", 20), vitals.get("focus", 0) + 5)
            math_msg = "[REST] You take a moment to recover. +5 Stamina, +2 HP, +5 Focus."
            
        elif "climb" in text and "climbable" in area_tags:
            vitals["stamina"] = max(0, vitals.get("stamina", 0) - 1)
            math_msg = "[TAG: CLIMBABLE] Found handholds in the rock. Climb successful with minimal exertion."
        elif "fire" in text:
            vitals["stamina"] = min(vitals.get("max_stamina", 12), vitals.get("stamina", 0) + 2)
            math_msg = "Fire built. +2 Stamina."
            
        return {"math_log": f"[SYSTEM Survival: {math_msg}]", "player_vitals": vitals}

    return {"math_log": "[SYSTEM: Action requires no math.]"}

async def chaos_check_node(state: GameState):
    """The Unpredictable Chaos Mechanic."""
    action = state["action_type"]
    chaos_numbers = state.get("chaos_numbers", [])
    if not chaos_numbers:
        chaos_numbers = [random.randint(1, 12)]
        
    unsure_actions = ["ATTACK", "SPELLCAST", "SURVIVAL", "TRAVEL", "MOVE", "STUNT"]
    if action not in unsure_actions:
        return {"chaos_strike": False, "chaos_numbers": chaos_numbers}
        
    chaos_roll = random.randint(1, 12)
    is_strike = chaos_roll in chaos_numbers
    chaos_narrative = ""
    vtt_commands = state.get("vtt_commands", [])
    
    if is_strike:
        log = state.get("math_log", "").lower()
        is_success = "victory" in log or "complete" in log or ("fire built" in log) or ("moving" in log) or ("cast" in log and "insufficient" not in log) or "climb successful" in log or "stunt" in log
        
        next_count = min(len(chaos_numbers) * 2, 6) 
        new_numbers = [random.randint(1, 12) for _ in range(next_count)]
        
        if is_success:
            chaos_narrative = "[CHAOS STRIKE: BENEFICIAL] The currents of fate fluctuate wildly, but your momentum carries you through! A strange shimmer surrounds your success."
        else:
            chaos_effects = [
                "A sudden warp in space disorients you.",
                "The atmosphere thickens with static, draining your focus.",
                "A localized tremor throws you off balance.",
                "Eldritch whispers cloud your vision.",
                "The ground momentarily liquifies underfoot."
            ]
            effect = random.choice(chaos_effects)
            chaos_narrative = f"[CHAOS STRIKE: HINDERING] Fate turns against you! {effect}"
            
            if random.random() < 0.4:
                chaos_narrative += " Something drawn by the chaos emerges..."
                vtt_commands.append("TRIGGER_CHAOTIC_ENCOUNTER")
        
        return {
            "chaos_strike": True, 
            "chaos_narrative": chaos_narrative, 
            "chaos_numbers": new_numbers,
            "vtt_commands": vtt_commands
        }
    
    return {"chaos_strike": False, "chaos_numbers": chaos_numbers}

async def director_node(state: GameState):
    """Tiered Narrative Director: Handles tension, weather, and quest placement."""
    tension = state.get("tension", 0)
    current_hex_id = int(state["current_location"] if state["current_location"].isdigit() else 0)
    hex_details = await api_gateway.get_hex_details(current_hex_id)
    biome = hex_details.get("biome", "Wilderness")
    
    biome_multipliers = {
        "Wasteland": 1.5, "Jungle": 1.3, "Swamp": 1.4, "Tundra": 1.5, "Plains": 1.0, "Forest": 1.1
    }
    multiplier = biome_multipliers.get(biome, 1.2)
    tension_gain = random.randint(2, 8) * multiplier
    tension += int(tension_gain)
    
    director_override = state.get("director_override") 
    vtt_commands = state.get("vtt_commands", [])
    active_encounter = state.get("active_encounter")

    if tension > 60 and random.random() < (tension - 40) / 100:
        tension = 0
        encounter_request = {
            "biome": biome,
            "threat_level": hex_details.get("threat_level", 2) + 1,
            "faction_territory": hex_details.get("faction_owner", "Wilderness")
        }
        encounter = await api_gateway.generate_encounter(encounter_request)
        if encounter:
            # Ensure the player token in the encounter has the correct sprite
            if "tokens" in encounter:
                for token in encounter["tokens"]:
                    if token.get("isPlayer"):
                        token["avatar_sprite"] = state.get("player_sprite")
            
            active_encounter = encounter
            director_override = f"[DIRECTOR OVERRIDE: TENSION BREAK] A sudden threat emerges from the {biome}!"
            vtt_commands.append(f"START_ENCOUNTER:{encounter['encounter_id']}")

    if state["action_type"] not in ["MOVE", "TRAVEL"]:
        return {"tension": tension, "director_override": director_override, "vtt_commands": vtt_commands, "active_encounter": active_encounter}
    
    is_regional_move = state["action_type"] == "TRAVEL"
    
    if is_regional_move and not state.get("active_regional_arcs"):
        idx = state["current_stage"]
        saga_beat = state["campaign_framework"][idx] if state.get("campaign_framework") else {}
        new_arcs = await api_gateway.generate_regional_arc(saga_beat, {"location": state["action_target"]})
        return {"tension": tension, "active_regional_arcs": new_arcs}

    pacing_goal = 2
    if state.get("campaign_framework") and state["current_stage"] < len(state["campaign_framework"]):
         pacing_goal = state["campaign_framework"][state["current_stage"]].get("pacing_milestones", 2)

    if state["current_stage_progress"] < pacing_goal and not state.get("active_local_quests") and random.random() < 0.3:
        side_quest = await api_gateway.generate_local_sidequest({"hex_id": state["action_target"]})
        if side_quest:
            return {"tension": tension, "active_local_quests": [side_quest]}

    return {"tension": tension, "director_override": director_override, "vtt_commands": vtt_commands, "active_encounter": active_encounter}

async def narrator_node(state: GameState):
    history_str = ""
    if state.get("chat_history"):
        for msg in state["chat_history"][-5:]:
            role = "TRAVELER" if msg["role"] == "user" else "NARRATOR"
            history_str += f"{role}: {msg['content']}\n"
    
    idx = state["current_stage"]
    saga = state["campaign_framework"][idx] if state.get("campaign_framework") else {"stage_name": "Prologue", "narrative_objective": "Survive"}
    pacing_goal = saga.get('pacing_milestones', 2)
    
    foresight_context = f"""
    --- SAGA STAGE: {saga['stage_name']} ---
    Global Goal: {saga.get('narrative_objective', 'None')}
    [WEATHER]: {state.get('weather')}
    [ACTIVE OBJECTIVES]:
    - Arcs: {[a['narrative_objective'] for a in state.get('active_regional_arcs', [])]}
    - Quests: {[l['narrative_objective'] for l in state.get('active_local_quests', [])]}
    [PACING]: {state['current_stage_progress']}/{pacing_goal} objectives cleared.
    [CHAOS STATUS]: {"STRIKE!" if state.get("chaos_strike") else "Stable"}
    """

    prompt = f"""
    You are the Director of T.A.L.E.W.E.A.V.E.R. (Gritty/Tactical).
    {history_str}
    Location: Hex {state['current_location']}
    Environment: {state.get('weather')}
    {foresight_context}
    System Result: {state['math_log']}
    Action: '{state['raw_chat_text']}'
    
    Narrate outcome in 3 gritty sentences. Mention the environment and tension if relevant.
    """
    
    if state.get("chaos_strike"):
        prompt += f"\n\nFOLLOW THIS CHAOS EVENT: {state['chaos_narrative']}"

    if state.get("director_override"):
        prompt += f"\n\nFOLLOW THIS: {state['director_override']}"

    if OLLAMA_AVAILABLE and local_llm:
        try:
            response = local_llm.invoke(prompt)
            narrative = response.strip()
        except: narrative = f"The {state.get('weather', 'world')} weighing heavily on you, you press on. (Offline)"
    else:
        narrative = f"[AI]: {prompt}"
        
    return {"ai_narration": narrative}

async def check_narrative_shift_node(state: GameState):
    """Refined: Random & Incidental Pacing Shift."""
    current_stage_idx = state["current_stage"]
    current_progress = state["current_stage_progress"]
    framework = state.get("campaign_framework", [])
    
    pacing_goal = 2
    if framework and current_stage_idx < len(framework):
        pacing_goal = framework[current_stage_idx].get("pacing_milestones", 2)

    log = state.get("math_log", "").lower()
    text = state.get("ai_narration", "").lower()
    
    # 1. Direct Objective Completion
    is_objective_clear = "objective complete" in text or "quest resolved" in text or ("clash result: victory" in log and state.get("active_local_quests")) or "saga_milestone" in log
    
    # 2. RANDOM/INCIDENTAL PROGRESS (User's Feedback)
    # Exceptional actions, Chaos Strikes, or just pure momentum
    incidental_chance = 0.0
    if state.get("chaos_strike"): incidental_chance += 0.15
    if "stunt" in log: incidental_chance += 0.10
    if "critical" in log: incidental_chance += 0.05
    
    is_incidental_hit = random.random() < incidental_chance

    if is_objective_clear or is_incidental_hit:
        current_progress += 1
        return {
            "current_stage_progress": current_progress,
            "active_local_quests": [],
            "active_errands": []
        }

    # Handle Stage Advance
    if current_progress >= pacing_goal and ("path revealed" in text or "saga continue" in text or random.random() < 0.05):
        new_stage = min(len(framework) - 1, current_stage_idx + 1)
        return {
            "current_stage": new_stage,
            "current_stage_progress": 0,
            "active_regional_arcs": []
        }

    return {"current_stage": current_stage_idx, "current_stage_progress": current_progress}

def create_director_graph():
    workflow = StateGraph(GameState)
    workflow.add_node("fetch_context", fetch_context_node)
    workflow.add_node("resolve_mechanics", resolve_mechanics_node)
    workflow.add_node("chaos_check", chaos_check_node)
    workflow.add_node("director", director_node)
    workflow.add_node("narrator", narrator_node)
    workflow.add_node("narrative_shift", check_narrative_shift_node)
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", "resolve_mechanics")
    workflow.add_edge("resolve_mechanics", "chaos_check")
    workflow.add_edge("chaos_check", "director")
    workflow.add_edge("director", "narrator")
    workflow.add_edge("narrator", "narrative_shift")
    workflow.add_edge("narrative_shift", END)
    return workflow.compile()
