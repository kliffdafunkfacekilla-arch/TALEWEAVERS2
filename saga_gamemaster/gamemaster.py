import json
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Paths to our God Engine data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PLAYER_FILE = os.path.join(DATA_DIR, "player_state.json")
MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")

# Define the State that LangGraph will pass between nodes
class GameState(TypedDict):
    player_id: str
    player_data: dict
    current_hex: dict
    weather: str
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
            "vitals": { "max_hp": 20 }
        }
    else:
        with open(PLAYER_FILE, "r") as f:
            player = json.load(f)
        
    # 2. Find where they are standing
    hex_x = player.get("location", {}).get("hex_x", 0)
    hex_y = player.get("location", {}).get("hex_y", 0)
    
    # 3. Read the Map
    if not os.path.exists(MAP_FILE):
        current_hex = {"biome": "Void", "faction_owner": "Unknown"}
    else:
        with open(MAP_FILE, "r") as f:
            world = json.load(f)
        
        # Find the specific hex data
        current_hex = next((h for h in world.get("macro_map", []) 
                            if h.get("x") == hex_x and h.get("y") == hex_y), 
                            {"biome": "Wasteland", "faction_owner": "No Man's Land"})
    
    # (Mocked weather for now, could ping Chronos API later)
    weather = "Heavy Snow and Freezing Winds" 
    
    return {
        "player_data": player, 
        "current_hex": current_hex, 
        "weather": weather
    }

# --- NODE 2: Generate the Scene ---
def generate_scene(state: GameState):
    print("GM is writing the scene...")
    # Attempt to initialize llama3 via Ollama
    try:
        llm = Ollama(model="llama3")
    except Exception as e:
        print(f"Ollama error: {e}. Falling back to echo.")
        return {"narrative_output": "The world is silent. (LLM offline)"}
    
    player_name = state["player_data"].get("name", "Traveler")
    health = state["player_data"].get("vitals", {}).get("max_hp", 0)
    biome = state["current_hex"].get("biome", "Wasteland")
    if not biome: biome = state["current_hex"].get("biome_tag", "Wasteland")
    faction = state["current_hex"].get("faction_owner", "No Man's Land")
    threat = state["current_hex"].get("threat_level", 1)
    
    # The Master Prompt
    system_prompt = f"""
    You are the Game Master of a gritty, dark-fantasy tabletop RPG called T.A.L.E.W.E.A.V.E.R.
    The tone is brutal, tactical, and survival-focused. 
    
    Current State:
    - Player Name: {player_name} (HP: {health})
    - Location: {biome} biome. 
    - Weather: {state['weather']}
    - Territory Controller: {faction}
    - Threat Level: {threat} out of 10.
    
    Write a 3-paragraph opening scene for the player arriving in this hex. 
    Incorporate the weather, the biome, and hint at the faction that owns the land. 
    Do not make decisions for the player. End by asking them what they want to do.
    """
    
    try:
        response = llm.invoke(system_prompt)
    except Exception as e:
        print(f"Invoke error: {e}")
        response = f"The {biome} stretches before you, controlled by {faction}. What do you do?"
        
    return {"narrative_output": response}

# --- BUILD THE GRAPH ---
workflow = StateGraph(GameState)

workflow.add_node("gather_context", gather_context)
workflow.add_node("generate_scene", generate_scene)

workflow.set_entry_point("gather_context")
workflow.add_edge("gather_context", "generate_scene")
workflow.add_edge("generate_scene", END)

# Compile the Engine
game_master_app = workflow.compile()

# --- TEST THE GM ---
if __name__ == "__main__":
    initial_state = {"player_id": "char_001", "player_data": {}, "current_hex": {}, "weather": "", "narrative_output": ""}
    # Using async invoke since most LangGraph tools are async ready, but keeping simple for this script
    result = game_master_app.invoke(initial_state)
    
    print("\n=== THE STORY BEGINS ===")
    print(result.get("narrative_output", "Silence..."))
