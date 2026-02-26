import json
import os
import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

# Paths to our God Engine data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PLAYER_FILE = os.path.join(DATA_DIR, "player_state.json")
MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")
WEAVER_URL = "http://localhost:8010/api/weaver/side_quest"

# Define the State that LangGraph will pass between nodes
class GameState(TypedDict):
    player_id: str
    player_data: dict
    current_hex: dict
    weather: str
    active_quest: Optional[dict]
    narrative_output: str

# --- NODE 1: Gather World State ---
def gather_context(state: GameState):
    print("GM is looking at the board...")
    
    # 1. Read Player
    if not os.path.exists(PLAYER_FILE):
        player = {
            "player_id": state["player_id"],
            "name": "Traveler",
            "location": { "hex_x": 0, "hex_y": 0 },
            "vitals": { "max_hp": 25 },
            "active_quests": []
        }
    else:
        with open(PLAYER_FILE, "r") as f:
            player = json.load(f)
        
    # 2. Find where they are standing
    hex_x = player.get("location", {}).get("hex_x", 0)
    hex_y = player.get("location", {}).get("hex_y", 0)
    
    # 3. Read the Map
    if not os.path.exists(MAP_FILE):
        current_hex = {"biome": "Void", "faction_owner": "Unknown", "id": 0}
    else:
        with open(MAP_FILE, "r") as f:
            world = json.load(f)
        
        # Find the specific hex data
        current_hex = next((h for h in world.get("macro_map", []) 
                            if h.get("x") == hex_x and h.get("y") == hex_y), 
                            {"biome": "Wasteland", "faction_owner": "No Man's Land", "id": 0})
    
    # (Mocked weather for now)
    weather = "Heavy Snow and Freezing Winds" 
    
    return {
        "player_data": player, 
        "current_hex": current_hex, 
        "weather": weather
    }

# --- NODE 2: Generate Active Quest (The Plot Twist) ---
async def generate_quest_beat(state: GameState):
    """Hits the Campaign Weaver to see if there is a story beat here."""
    print("GM is weaving the plot...")
    
    biome = state["current_hex"].get("biome", "wilderness")
    faction = state["current_hex"].get("faction_owner", "No Man's Land")
    
    quest_request = {
        "seed": f"A tactical dilemma in the {biome} involving {faction}.",
        "location": f"Hex_{state['current_hex'].get('id', 'unknown')}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(WEAVER_URL, json=quest_request, timeout=10.0)
            if response.status_code == 200:
                print("GM found a story beat.")
                return {"active_quest": response.json()}
    except Exception as e:
        print(f"Weaver offline: {e}")
        
    return {"active_quest": None}

# --- NODE 3: Generate the Scene ---
def generate_scene(state: GameState):
    print("GM is writing the scene...")
    try:
        llm = Ollama(model="llama3")
    except Exception as e:
        return {"narrative_output": "The world is silent. (LLM offline)"}
    
    player_name = state["player_data"].get("name", "Traveler")
    health = state["player_data"].get("vitals", {}).get("max_hp", 0)
    biome = state["current_hex"].get("biome", "Wasteland")
    faction = state["current_hex"].get("faction_owner", "No Man's Land")
    
    quest_text = ""
    if state.get("active_quest"):
        obj = state["active_quest"].get("narrative_objective", "Wait for further instructions.")
        quest_text = f"\nQUEST OBJECTIVE: {obj}"

    # The Master Prompt
    system_prompt = f"""
    You are the Game Master of a gritty, dark-fantasy tabletop RPG called T.A.L.E.W.E.A.V.E.R.
    The tone is brutal, tactical, and survival-focused. 
    
    Current State:
    - Player Name: {player_name} (HP: {health})
    - Location: {biome} biome. 
    - Weather: {state['weather']}
    - Territory Controller: {faction}
    {quest_text}
    
    Write a 3-paragraph opening scene for the player arriving in this hex. 
    Incorporate the weather, the biome, the faction, and the quest objective if present. 
    Do not make decisions for the player. End by asking them what they want to do.
    """
    
    try:
        response = llm.invoke(system_prompt)
    except:
        response = f"The {biome} stretches before you. {quest_text}. What do you do?"
        
    return {"narrative_output": response}

# --- BUILD THE GRAPH ---
workflow = StateGraph(GameState)

workflow.add_node("gather_context", gather_context)
workflow.add_node("generate_quest_beat", generate_quest_beat)
workflow.add_node("generate_scene", generate_scene)

workflow.set_entry_point("gather_context")
workflow.add_edge("gather_context", "generate_quest_beat")
workflow.add_edge("generate_quest_beat", "generate_scene")
workflow.add_edge("generate_scene", END)

# Compile
game_master_app = workflow.compile()

# --- TEST ---
if __name__ == "__main__":
    import asyncio
    initial_state = {"player_id": "char_001", "player_data": {}, "current_hex": {}, "weather": "", "active_quest": None, "narrative_output": ""}
    
    async def run_test():
        result = await game_master_app.ainvoke(initial_state)
        print("\n=== THE STORY BEGINS ===")
        print(result.get("narrative_output", "Silence..."))
        
    asyncio.run(run_test())
