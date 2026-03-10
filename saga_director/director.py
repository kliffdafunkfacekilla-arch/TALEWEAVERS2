import json
import os
import random
import httpx
from langchain_core.prompts import ChatPromptTemplate
try:
    from langchain_ollama import OllamaLLM
    local_llm = OllamaLLM(model="llama3")
    OLLAMA_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.llms import Ollama
        local_llm = Ollama(model="llama3")
        OLLAMA_AVAILABLE = True
    except:
        local_llm = None
        OLLAMA_AVAILABLE = False
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List

# Paths - Unified to root /data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PLAYER_FILE = os.path.join(DATA_DIR, "player_state.json")
MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")
CHRONICLE_FILE = os.path.join(DATA_DIR, "Chronicle_Log.json")
WEAVER_URL = "http://localhost:8010/api/weaver/sidequest"

# Define the State that LangGraph will pass between nodes
class GameState(TypedDict):
    player_id: str
    player_data: dict
    current_hex: dict
    weather: str
    active_quest: Optional[dict]
    active_encounter: Optional[dict]  # New: Stores the mechanical encounter from Module 4
    war_events: List[str]
    tension: int
    event_trigger: Optional[str]
    narrative_output: str

# --- NODE 1: Gather World State ---
def gather_context(state: GameState):
    print("Director is looking at the board...")
    
    # 1. Read Player
    if not os.path.exists(PLAYER_FILE):
        player = {
            "player_id": state["player_id"],
            "name": "Traveler",
            "location": { "hex_x": 0, "hex_y": 0 },
            "vitals": { "hp": 25, "max_hp": 25 },
            "tension": 0,
            "active_quests": []
        }
    else:
        with open(PLAYER_FILE, "r", encoding='utf-8') as f:
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
        current_hex = next((h for h in world.get("macro_map", []) 
                            if h.get("x") == hex_x and h.get("y") == hex_y), 
                            {"biome": "Wasteland", "faction_owner": "No Man's Land", "id": 0})
    
    # 4. Read Chronicle (Distant War Awareness)
    war_notes = []
    if os.path.exists(CHRONICLE_FILE):
        with open(CHRONICLE_FILE, "r") as f:
            logs = json.load(f)
            # Find the last few events to narrate
            for log in logs[-3:]:
                war_notes.append(log.get("description", ""))

    weather = "Heavy Snow and Freezing Winds" 
    
    return {
        "player_data": player, 
        "current_hex": current_hex, 
        "war_events": war_notes,
        "tension": player.get("tension", 0),
        "weather": weather
    }

# --- NODE 2: evaluate_tension (The Director Pulse) ---
def evaluate_tension(state: GameState):
    """Calculates if an immediate event should occur based on noise/lingering."""
    tension = state.get("tension", 0)
    event_trigger = None
    
    # If threat level is high, tension rises faster
    threat = state["current_hex"].get("threat_level", 1)
    tension += random.randint(1, 5) + threat
    
    # Roll for a pulse event
    roll = random.randint(1, 100)
    if tension > 50 and roll < (tension - 40):
        print("Tension peak! Triggering event...")
        event_trigger = random.choice(["AMBUSH", "HUNTED", "GEAR_BREAK"])
        tension = 0 # Reset after trigger
    elif roll < 5:
        event_trigger = "LUCKY_FIND"
        
    return {"tension": tension, "event_trigger": event_trigger}

# --- NODE 3: Generate Active Quest (The Plot Twist) ---
async def generate_quest_beat(state: GameState):
    """Hits the Campaign Weaver to see if there is a story beat here."""
    if state.get("event_trigger"):
        return {"active_quest": None} # Skip weaver if we have a tension event

    print("Director is weaving the plot...")
    biome = state["current_hex"].get("biome", "wilderness")
    faction = state["current_hex"].get("faction_owner", "No Man's Land")
    
    quest_request = {
        "hex_context": {
            "biome": biome,
            "faction_owner": faction,
            "hex_id": state['current_hex'].get('id', 'unknown')
        },
        "context_packet": state.get("player_data")
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(WEAVER_URL, json=quest_request, timeout=10.0)
            if response.status_code == 200:
                print("Director found a story beat.")
                return {"active_quest": response.json()}
    except Exception as e:
        print(f"Weaver offline: {e}")
        
    return {"active_quest": None}

# --- NODE 4: Generate the Scene ---
def generate_scene(state: GameState):
    print("Director is writing the scene...")
    if not OLLAMA_AVAILABLE or not local_llm:
        return {"narrative_output": "The world is silent. (LLM offline)"}
    
    p = state["player_data"]
    hp_pct = (p.get("vitals", {}).get("hp", 0) / p.get("vitals", {}).get("max_hp", 1)) * 100
    
    war_context = "\nDISTANT EVENTS: " + " ".join(state["war_events"]) if state["war_events"] else ""
    quest_text = f"\nQUEST OBJECTIVE: {state['active_quest']['narrative_objective']}" if state.get("active_quest") else ""
    
    event_text = ""
    if state.get("event_trigger"):
        event_text = f"\nCRITICAL EVENT: {state['event_trigger']}. Acknowledge this immediately in the narration!"

    health_style = "Survival Mode" if hp_pct < 50 else "Standard"

    # The Master Prompt
    system_prompt = f"""
    You are the Director of T.A.L.E.W.E.A.V.E.R. 
    Tone: Gritty, Brutal, Tactical.
    
    Player: {p.get('name')} (HP: {p.get('vitals', {}).get('hp')}/{p.get('vitals', {}).get('max_hp')})
    Location: {state['current_hex'].get('biome')} (Owned by {state['current_hex'].get('faction_owner')})
    Style: {health_style} {war_context} {quest_text} {event_text}
    
    NARRATION RULES:
    1. If HP is low, describe their physical pain and fatigue.
    2. If DISTANT EVENTS are present, mention sensory clues (smoke, distant sounds).
    3. If CRITICAL EVENT is set, narrate the transition into danger (e.g. an ambush).
    4. Write 3 paragraphs. End with a prompt.
    """
    
    try:
        response = local_llm.invoke(system_prompt)
    except:
        response = f"The {state['current_hex'].get('biome')} stretches before you. {event_text}. What do you do?"
        
    return {"narrative_output": response}

# --- BUILD THE GRAPH ---
workflow = StateGraph(GameState)

workflow.add_node("gather_context", gather_context)
workflow.add_node("evaluate_tension", evaluate_tension)
workflow.add_node("generate_quest_beat", generate_quest_beat)
workflow.add_node("generate_scene", generate_scene)

workflow.set_entry_point("gather_context")
workflow.add_edge("gather_context", "evaluate_tension")
workflow.add_edge("evaluate_tension", "generate_quest_beat")
workflow.add_edge("generate_quest_beat", "generate_scene")
workflow.add_edge("generate_scene", END)

saga_director_app = workflow.compile()

if __name__ == "__main__":
    import asyncio
    initial_state = {
        "player_id": "char_001", 
        "player_data": {}, 
        "current_hex": {}, 
        "weather": "", 
        "active_quest": None, 
        "war_events": [], 
        "tension": 0, 
        "event_trigger": None, 
        "narrative_output": ""
    }
    
    async def run_test():
        result = await saga_director_app.ainvoke(initial_state)
        print("\n=== THE STORY BEGINS ===")
        print(result.get("narrative_output", "Silence..."))
        
    asyncio.run(run_test())
