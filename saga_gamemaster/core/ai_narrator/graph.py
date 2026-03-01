from langgraph.graph import StateGraph, END
from core.ai_narrator.state import GameState
from core.api_gateway import SAGA_API_Gateway
import asyncio
import json
import logging

api_gateway = SAGA_API_Gateway()

# ── Initialize Local AI Brain via Ollama ──
# Change "llama3" to whatever model you have downloaded (e.g., "mistral", "phi3", "gemma")
try:
    from langchain_community.llms import Ollama
    local_llm = Ollama(model="llama3")
    OLLAMA_AVAILABLE = True
    print("[NARRATOR] Ollama LLM initialized (model: llama3)")
except ImportError:
    local_llm = None
    OLLAMA_AVAILABLE = False
    print("[NARRATOR] langchain-community not installed. Falling back to prompt echo.")
except Exception as e:
    local_llm = None
    OLLAMA_AVAILABLE = False
    print(f"[NARRATOR] Ollama initialization failed: {e}. Falling back to prompt echo.")


async def fetch_context_node(state: GameState):
    campaign_data = await api_gateway.get_campaign_state(state["player_id"])
    
    # DO NOT overwrite vitals if they already exist in state (preserves changes from mechanics)
    vitals = state.get("player_vitals")
    if not vitals:
        char_data = await api_gateway.get_character(state["player_id"])
        vitals = char_data["survival_pools"]
    
    return {
        "current_location": campaign_data["current_node_name"],
        "active_quests": campaign_data["active_quests"],
        "player_vitals": vitals
    }

async def resolve_mechanics_node(state: GameState):
    action = state["action_type"]
    target = state["action_target"]
    
    if action == "USE_ITEM":
        result = await api_gateway.use_item(state["player_id"], target)
        return {"math_log": f"[SYSTEM: {result['item_name']} consumed. {result['effect']} applied.]"}
    
    elif action == "ATTACK":
        # Build CombatantState dicts from the real player_vitals
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
            "name": target,
            "current_hp": 15,
            "attack_or_defense_pool": 4,
            "weapon_damage_dice": "1d6",
            "stamina_burned": 0,
            "focus_burned": 0
        }
        result = await api_gateway.resolve_clash(attacker_data, defender_data)
        injury_text = f" Injury: {result['injury']}" if result.get("injury") else ""
        return {"math_log": f"[SYSTEM: Clash Result: {result['margin']}. Damage: {result['dmg']}.{injury_text}]"}
    
    elif action == "MOVE" or action == "TRAVEL":
        return {"math_log": f"[SYSTEM: Moving to {target}.]"}
    
    elif action in ["PERSUADE", "INTIMIDATE"]:
        # Social Combat Resolver
        vitals = state.get("player_vitals", {})
        enc = state.get("active_encounter")
        if not enc or not enc["data"].get("npcs"):
            return {"math_log": "[SYSTEM: No one here to talk to.]"}
        
        npc = enc["data"]["npcs"][0] # Target first NPC for now
        attacker_pool = state.get("attributes", {}).get("charm" if action == "PERSUADE" else "might", 5) + state.get("stamina_burned", 0)
        defender_pool = npc.get("willpower", 4)
        
        result = await api_gateway.resolve_clash(
            {"name": state["player_id"], "attack_or_defense_pool": attacker_pool, "stamina_burned": state.get("stamina_burned", 0)},
            {"name": npc["name"], "attack_or_defense_pool": defender_pool, "stamina_burned": 0}
        )
        
        dmg = result["dmg"]
        npc["composure_pool"] = max(0, npc["composure_pool"] - dmg)
        
        outcome = "SUCCESS" if npc["composure_pool"] == 0 else "CONTINUE"
        return {
            "math_log": f"[SYSTEM: Social Clash ({action}). Result: {result['margin']}. Composure Damage: {dmg}. {npc['name']} Composure: {npc['composure_pool']}]",
            "active_encounter": enc if outcome == "CONTINUE" else None # Close encounter if composure breaks
        }

    elif action in ["DISARM", "EVADE"]:
        # Hazard Resolver
        enc = state.get("active_encounter")
        if not enc or enc["data"].get("category") != "HAZARD":
            return {"math_log": "[SYSTEM: No hazard detected.]"}
        
        hazard = enc["data"]
        check = hazard["disarm_check"] if action == "DISARM" else hazard["detection_check"]
        roll = random.randint(1, 20) + 5 # Mocking attribute bonus
        
        if roll >= check["dc"]:
            return {
                "math_log": f"[SYSTEM: Hazard {action} SUCCESS! Rolled {roll} vs DC {check['dc']}]",
                "active_encounter": None 
            }
        else:
            damage = hazard["trigger_effect"]["damage"]
            injury = hazard["trigger_effect"]["injury"]
            return {
                "math_log": f"[SYSTEM: Hazard TRIGGERED! Rolled {roll} vs DC {check['dc']}. Damage: {damage}. Injury: {injury}]",
                "active_encounter": None
            }

    elif action == "CHOICE":
        # Dilemma Resolver
        enc = state.get("active_encounter")
        if not enc or enc["data"].get("category") != "DILEMMA":
            return {"math_log": "[SYSTEM: No dilemma active.]"}
        
        # Apply mechanical effect (Mocked for now)
        return {
            "math_log": f"[SYSTEM: Choice '{target}' made. Applying consequences...]",
            "active_encounter": None
        }

    elif action == "SURVIVAL":
        vitals = state.get("player_vitals", {})
        text = state.get("raw_chat_text", "").lower()
        
        math_msg = ""
        if "fire" in text or "bonfire" in text:
            # Restore some focus/stamina
            vitals["stamina"] = min(vitals.get("max_stamina", 12), vitals.get("stamina", 0) + 2)
            math_msg = "Fire built. +2 Stamina."
        if "cook" in text or "meal" in text or "eat" in text:
            # Restore HP
            vitals["current_hp"] = min(vitals.get("max_hp", 20), vitals.get("current_hp", 0) + 3)
            math_msg += " Meal prepared. +3 HP."
        if "rest" in text or "sleep" in text:
            vitals["focus"] = min(vitals.get("max_focus", 10), vitals.get("focus", 0) + 4)
            math_msg += " Rested. +4 Focus."
            
        return {
            "math_log": f"[SYSTEM Survival: {math_msg}]",
            "player_vitals": vitals
        }

    return {"math_log": "[SYSTEM: Action requires no math.]"}

async def director_node(state: GameState):
    # Only roll for NEW encounters during movement
    if state["action_type"] not in ["MOVE", "TRAVEL"]:
        return {
            "math_log": "",
            "director_override": None,
            "vtt_commands": [],
            "active_encounter": state.get("active_encounter"), # PERSIST EXISTING ENCOUNTER
            "ai_narration": ""
        }
    
    coords = state["action_target"]
    trigger = await api_gateway.check_quest_triggers(coords)
    
    encounter_request = {
        "biome": state.get("current_location", "Wilderness"),
        "threat_level": 2, # Fixed for now
        "faction_territory": "The Wolf Cult" if trigger else "Wilderness"
    }

    if trigger:
        # 1. Prompted Generation (Quest/Event)
        encounter_request.update({
            "forced_type": trigger["type"],
            "seed_prompt": trigger.get("seed")
        })
        encounter = await api_gateway.generate_encounter(encounter_request)
    else:
        # 2. Random Chance (Director Pulse)
        import random
        if random.random() < 0.15: # 15% chance for a random encounter per move
            encounter = await api_gateway.generate_encounter(encounter_request)
        else:
            encounter = None

    if encounter:
        enc_data = encounter["data"]
        
        # --- NEW: Map enemies/NPCs to VTT Tokens ---
        tokens = []
        
        # 1. Inject Player Token
        vitals = state.get("player_vitals", {})
        tokens.append({
            "id": "PLAYER_001",
            "name": state.get("player_id", "Player"),
            "label": state.get("player_id", "Player"),
            "x": 5, # Center of tactical grid
            "y": 5,
            "color": 0x4ade80,
            "isPlayer": True,
            "current_hp": vitals.get("current_hp", 20),
            "max_hp": vitals.get("max_hp", 20),
            "stamina": vitals.get("stamina", 12),
            "composure": vitals.get("composure", 10)
        })

        # 2. Map Enemies or NPCs
        if enc_data.get("category") == "COMBAT" and "enemies" in enc_data:
            for idx, enemy in enumerate(enc_data["enemies"]):
                spatial = enemy.get("spatial", {})
                tokens.append({
                    "id": f"enemy_{idx}",
                    "name": enemy.get("name", "Enemy"),
                    "label": enemy.get("name", "Enemy"),
                    "x": 10 + idx, # Place enemies offset from player
                    "y": 5,
                    "color": 0xef4444,
                    "isPlayer": False,
                    "current_hp": enemy.get("hp", 15),
                    "max_hp": enemy.get("hp", 15),
                    "attack_or_defense_pool": enemy.get("stamina", 5),
                    "weapon_dice": enemy.get("weapons", ["1d6"])[0] if enemy.get("weapons") else "1d6"
                })
        elif enc_data.get("category") == "SOCIAL" and "npcs" in enc_data:
            for idx, npc in enumerate(enc_data["npcs"]):
                tokens.append({
                    "id": f"npc_{idx}",
                    "name": npc.get("name", "NPC"),
                    "label": npc.get("name", "NPC"),
                    "x": 8,
                    "y": 5,
                    "color": 0x60a5fa,
                    "isPlayer": False,
                    "composure_pool": npc.get("composure_pool", 10),
                    "willpower": npc.get("willpower", 4)
                })

        # Attach tokens to the encounter
        encounter["tokens"] = tokens

        override_prompt = f"""
        [DIRECTOR OVERRIDE: {enc_data['category']} ENCOUNTER DETECTED]
        Title: {enc_data['title']}
        Initial Narrative: {enc_data['narrative_prompt']}
        """
        
        commands = [f"START_ENCOUNTER:{encounter['encounter_id']}"]
        return {
            "director_override": override_prompt,
            "vtt_commands": commands,
            "active_encounter": encounter
        }
    
    return {"director_override": None, "vtt_commands": [], "active_encounter": None}

async def narrator_node(state: GameState):
    """Node 3: The True AI Director — powered by local Ollama LLM."""
    print("[GRAPH] Node 3: Generating Narration...")
    
    # Build the prompt with mechanical context and history
    history_str = ""
    if state.get("chat_history"):
        for msg in state["chat_history"]:
            role = "TRAVELER" if msg["role"] == "user" else "NARRATOR"
            history_str += f"{role}: {msg['content']}\n"
    
    encounter_context = ""
    if state.get("active_encounter"):
        enc = state["active_encounter"]["data"]
        encounter_context = f"\nACTIVE ENCOUNTER: {enc['title']} ({enc['category']})\nMechanical Data: {json.dumps(enc)}"

    prompt = f"""
    You are the Game Master of the S.A.G.A. Engine, a gritty, dark-fantasy survival game.
    
    --- CONVERSATION HISTORY ---
    {history_str}

    --- HIDDEN WORLD STATE ---
    Location: {state['current_location']}
    Player Vitals: {state['player_vitals']}{encounter_context}
    
    --- MECHANICAL TRUTH (DO NOT CONTRADICT THIS) ---
    {state['math_log']}
    """
    
    if state.get("director_override"):
        prompt += f"\n\n{state['director_override']}\nWrite the narration in 2 to 3 sentences of gritty tone. Do not use UI terminology."
    else:
        prompt += f"\n\nPlayer Action: '{state['raw_chat_text']}'\nWrite exactly 2 to 3 sentences of visceral, gritty narration describing the outcome based strictly on the Mechanical Truth above."

    # Try the real Ollama LLM first, fall back to prompt echo
    if OLLAMA_AVAILABLE and local_llm is not None:
        try:
            print("[GRAPH] Firing prompt to Ollama...")
            response = local_llm.invoke(prompt)
            narrative = response.strip()
        except Exception as e:
            print(f"[OLLAMA ERROR] {e}")
            narrative = f"The {state['current_location']} remains silent. (Ollama Offline)"
    else:
        narrative = f"[AI LLM PROMPT GENERATED]:\n{prompt}"
        
    return {"ai_narration": narrative}

def create_director_graph():
    workflow = StateGraph(GameState)
    
    workflow.add_node("fetch_context", fetch_context_node)
    workflow.add_node("resolve_mechanics", resolve_mechanics_node)
    workflow.add_node("director", director_node)
    workflow.add_node("narrator", narrator_node)
    
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", "resolve_mechanics")
    workflow.add_edge("resolve_mechanics", "director")
    workflow.add_edge("director", "narrator")
    workflow.add_edge("narrator", END)
    
    return workflow.compile()
