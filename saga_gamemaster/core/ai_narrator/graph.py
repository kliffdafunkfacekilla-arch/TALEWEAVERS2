from langgraph.graph import StateGraph, END
from saga_gamemaster.core.ai_narrator.state import GameState
from saga_gamemaster.core.api_gateway import SAGA_API_Gateway
import asyncio

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
    char_data = await api_gateway.get_character(state["player_id"])
    
    return {
        "current_location": campaign_data["current_node_name"],
        "active_quests": campaign_data["active_quests"],
        "player_vitals": char_data["survival_pools"]
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
    
    return {"math_log": "[SYSTEM: Action requires no math.]"}

async def director_node(state: GameState):
    if state["action_type"] not in ["MOVE", "TRAVEL"]:
        return {"director_override": None, "vtt_commands": []}
    
    coords = state["action_target"]
    trigger = await api_gateway.check_quest_triggers(coords)
    
    if trigger and trigger["type"] == "AMBUSH":
        override_prompt = f"""
        [DIRECTOR OVERRIDE: 
        The player stepped into Hex {coords}. 
        This is the location of the 'Bandit Ambush' quest trigger.
        Ignore the player's intended movement. 
        Narrate 3 Wolf Cultists dropping from the trees, weapons drawn.
        Demand they hand over their Aetherium coins.]
        """
        commands = ["LOCK_UI", f"SPAWN_ENEMIES:Wolf_Cultist:3:coords_{coords}"]
        return {
            "director_override": override_prompt,
            "vtt_commands": commands
        }
    
    return {"director_override": None, "vtt_commands": []}

async def narrator_node(state: GameState):
    """Node 3: The True AI Director — powered by local Ollama LLM."""
    print("[GRAPH] Node 3: Generating Narration...")
    
    # Build the ironclad prompt that prevents the AI from hallucinating rules
    prompt = f"""
    You are the Game Master of the S.A.G.A. Engine, a gritty, dark-fantasy survival game.
    
    --- HIDDEN WORLD STATE ---
    Location: {state['current_location']}
    Player Vitals: {state['player_vitals']}
    Active Quests: {state['active_quests']}
    
    --- MECHANICAL TRUTH (DO NOT CONTRADICT THIS) ---
    {state['math_log']}
    """
    
    if state.get("director_override"):
        prompt += f"\n\n{state['director_override']}\nWrite the narration in 2 sentences."
    else:
        prompt += f"\n\nPlayer Action: '{state['raw_chat_text']}'\nWrite exactly 2 to 3 sentences of visceral, gritty narration describing the outcome of the player's action based strictly on the Mechanical Truth above. Do not mention stats, dice, or the math log directly in your response. Describe the physical, in-world result."

    # Try the real Ollama LLM first, fall back to prompt echo
    if OLLAMA_AVAILABLE and local_llm is not None:
        try:
            print("[GRAPH] Firing prompt to Ollama...")
            response = local_llm.invoke(prompt)
            narrative = response.strip()
            print(f"[GRAPH] Ollama response received ({len(narrative)} chars)")
        except Exception as e:
            print(f"[OLLAMA ERROR] Failed to reach local AI: {e}")
            narrative = "[SYSTEM ERR] The AI Director (Ollama) is offline or the model name is incorrect. Ensure Ollama is running."
    else:
        # Fallback: echo the prompt so the pipeline still works without Ollama
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
