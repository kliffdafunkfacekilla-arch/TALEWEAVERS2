import json
import os
import re
import httpx
from typing import List, Optional
from core.schemas import CampaignRoadmap, QuestNode
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Centralized Data Path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")

async def fetch_world_data() -> dict:
    """Reads the master world data from the centralized data directory."""
    print(f"DEBUG: Looking for map at {MAP_FILE}")
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r") as f:
                data = json.load(f)
                print(f"DEBUG: Loaded map data successfully.")
                return data
        except Exception as e:
            print(f"DEBUG: Failed to load map: {e}")
    return {"world_name": "Shatterlands", "regions": [], "macro_map": []}

def parse_json_garbage(text: str) -> dict:
    """Cleaner for LLM output including markdown blocks."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    return {}

async def generate_roadmap(world_id: str, starting_hex: str, theme: Optional[str] = None) -> CampaignRoadmap:
    # 1. Gather Context
    world_data = await fetch_world_data()
    
    # 2. Setup LLM
    llm = Ollama(model="llama3")
    
    # 3. Create Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver. "
                   "Generate a structured 5-step quest roadmap based on world data. "
                   "You MUST output raw JSON following this schema: "
                   "{schema}"),
        ("user", "World Data: {world_context}\nTheme: {theme}\nStarting Hex: {hex}\n"
                 "Generate a multi-step campaign. Use regional factions and terrain context.")
    ])
    
    # Define schema for the prompt
    schema_str = json.dumps(CampaignRoadmap.model_json_schema(), indent=2)
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "schema": schema_str,
            "world_context": json.dumps(world_data)[:2000], # Trucate for token limits
            "theme": theme or "Grimdark Fantasy",
            "hex": starting_hex
        })
        parsed = parse_json_garbage(response)
        return CampaignRoadmap(**parsed)
    except Exception as e:
        print(f"Roadmap generation failed, using fallback: {e}")
        return CampaignRoadmap(
            campaign_name="The Shattered Silence",
            main_antagonist_faction="Unknown Threat",
            starting_location=starting_hex,
            quest_nodes=[
                QuestNode(step_number=1, narrative_objective="Survey the immediate surroundings.", trigger_location=starting_hex, encounter_type="DISCOVERY", success_state_change="UNLOCK_STEP_2")
            ]
        )

async def generate_mini_quest(seed: str, location: str) -> QuestNode:
    llm = Ollama(model="llama3")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver. "
                   "Generate a single, self-contained mini-quest step. "
                   "Output ONLY raw JSON matching this schema: {schema}"),
        ("user", "Seed: {seed}\nLocation: {location}")
    ])
    
    schema_str = json.dumps(QuestNode.model_json_schema(), indent=2)
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "schema": schema_str,
            "seed": seed,
            "location": location
        })
        parsed = parse_json_garbage(response)
        if "step_number" not in parsed: parsed["step_number"] = 1
        return QuestNode(**parsed)
    except Exception as e:
        print(f"Mini-quest generation failed, using fallback: {e}")
        return QuestNode(
            step_number=1,
            narrative_objective=f"Investigate the anomaly at {location}.",
            trigger_location=location,
            encounter_type="HAZARD",
            success_state_change="REVEAL_LOOT"
        )
