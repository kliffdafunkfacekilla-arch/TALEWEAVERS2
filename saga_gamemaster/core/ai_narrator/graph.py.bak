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
        result = await api_gateway.resolve_clash(state["player_id"], target)
        return {"math_log": f"[SYSTEM: Clash Result: {result['margin']}. Damage: {result['dmg']}]"}
    
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
    # This would normally call an LLM. For now, we mock the result.
    context = f"Location: {state['current_location']}, Vitals: {state['player_vitals']}"
    math = state["math_log"]
    override = state.get("director_override", "")
    
    # Logic to build prompt and call LLM
    narrative = f"The GM narrates: {state['raw_chat_text']} {math}"
    if override:
        narrative = f"SUDDENLY! {override}\n{math}"
        
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
