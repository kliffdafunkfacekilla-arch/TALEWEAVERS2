from langgraph.graph import StateGraph, END
from saga_gamemaster.core.ai_narrator.state import GameState
from saga_gamemaster.core.api_gateway import SAGA_API_Gateway
import asyncio

api_gateway = SAGA_API_Gateway()

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
    # This is the exact prompt structure that prevents the AI from hallucinating rules.
    prompt = f"""
    You are the gritty, tactical Game Master of the T.A.L.E.W.E.A.V.E.R. Engine.
    
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
        prompt += f"\n\nPlayer Action: '{state['raw_chat_text']}'\nWrite 2 sentences of narration describing the Mechanical Truth."

    # In production, you will call LangChain here:
    # response = await llm.ainvoke(prompt)
    # narrative = response.content
    
    # For testing the pipeline immediately without an OpenAI key:
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
