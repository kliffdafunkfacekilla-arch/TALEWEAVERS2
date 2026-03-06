import json
import os
import re
import httpx
from typing import List, Optional
from core.schemas import CampaignRoadmap, QuestNode, CampaignFramework, StoryArcStage
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MAP_FILE = os.path.join(DATA_DIR, "Saga_Master_World.json")

async def fetch_world_data() -> dict:
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"world_name": "Shatterlands", "regions": [], "macro_map": []}

def parse_json_garbage(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try: return json.loads(match.group(0))
        except: pass
    return {}

async def generate_campaign_framework(characters: List[dict], world_state: dict, settings: dict, history: Optional[List[dict]] = None, context_packet: Optional[dict] = None) -> CampaignFramework:
    """Generates or adjusts a full 8-stage Hero's Journey arc."""
    llm = Ollama(model="llama3")
    
    mode = "INITIAL GENERATION" if not history else "DYNAMIC ADJUSTMENT"
    
    length_setting = settings.get("length", "SAGA")
    pacing_instruction = "between 2 to 3"
    if length_setting == "ONE_SHOT": pacing_instruction = "exactly 1"
    elif length_setting == "EPIC": pacing_instruction = "between 4 to 6"
    
    living_context = ""
    if context_packet:
        living_context = f"\nLIVING CONTEXT:\n{json.dumps(context_packet, indent=2)}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver (Mode: {mode}). "
                   "IMPORTANT: You MUST analyze the provided 'World State' and 'Living Context' JSON data. "
                   "Identify factions that are expanding, starving, or at war. "
                   "Generate an 8-stage 'Hero's Journey' campaign framework that actively intervenes in or revolves around these simulated, ongoing events. "
                   "STAGES: Call to Adventure, Refusal of the Call, Crossing the Threshold, "
                   "Tests/Allies/Enemies, Approach to the Inmost Cave, The Ordeal, The Reward, Road Back. "
                   "Each stage needs a plot_point, narrative_objective, and a foreshadowing_clue. "
                   f"IMPORTANT: Each stage must also have 'pacing_milestones' ({pacing_instruction}). "
                   "Output ONLY raw JSON matching this schema: {{schema}}"),
        ("user", "Characters: {characters}\nWorld State: {world_context}\nLiving Context: {living_context}\nSettings: {settings}\nRecent History: {history}")
    ])
    
    schema_str = json.dumps(CampaignFramework.model_json_schema(), indent=2)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "schema": schema_str,
            "characters": json.dumps(characters),
            "world_context": json.dumps(world_state)[:2000],
            "living_context": living_context,
            "settings": json.dumps(settings),
            "history": json.dumps(history or [])
        })
        parsed = parse_json_garbage(response)
        return CampaignFramework(**parsed)
    except Exception as e:
        print(f"Framework generation failed: {e}")
        return CampaignFramework(arc_name="A Bound Destiny", theme="Survival", hero_journey=[StoryArcStage(stage_name="Placeholder", plot_point="N/A", narrative_objective="Continue", foreshadowing_clue="N/A", pacing_milestones=2) for _ in range(8)], character_hooks=[])

async def generate_regional_arc(saga_beat: dict, region_context: dict, context_packet: Optional[dict] = None) -> List[QuestNode]:
    """Tier 2: Generates a 2-3 step sub-plot bridging two Saga Beats."""
    llm = Ollama(model="llama3")
    
    living_context = ""
    if context_packet:
        living_context = f"\nLIVING CONTEXT:\n{json.dumps(context_packet, indent=2)}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver (Tier: ARC). "
                   "Generate a 2-step 'Regional Arc' that bridges the player's current position to the next Saga Beat. "
                   "IMPORTANT: Examine the Region data and the Living Context. Identify any specific factions, threats, or locations active here. "
                   "Provide specific values for 'target_entity', 'employer_or_faction', and 'local_impact_description' based on this simulated data. "
                   "Include a 'target_node_id' if the objective is tied to a specific landmark. "
                   "Output ONLY raw JSON as a list of QuestNodes."),
        ("user", "Saga Beat: {saga}\nRegion: {region}\nLiving Context: {living_context}")
    ])
    try:
        response = await (prompt | llm).ainvoke({
            "saga": json.dumps(saga_beat), 
            "region": json.dumps(region_context),
            "living_context": living_context
        })
        parsed = parse_json_garbage(response)
        return [QuestNode(**q) for q in (parsed if isinstance(parsed, list) else [])]
    except: return []

async def generate_local_sidequest(hex_context: dict, context_packet: Optional[dict] = None) -> QuestNode:
    """Tier 3: Generates a hex-specific side quest."""
    llm = Ollama(model="llama3")
    
    living_context = ""
    if context_packet:
        living_context = f"\nLIVING CONTEXT:\n{json.dumps(context_packet, indent=2)}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver (Tier: SIDE_QUEST). "
                   "Generate a single, self-contained mini-quest step. "
                   "IMPORTANT: Examine the Location data and Living Context. Use specific NPCs, Rumours, or Faction attitudes provided. "
                   "Name a specific 'target_entity' and a specific 'employer_or_faction'. "
                   "Describe the 'local_impact_description' to emphasize why this matters to the simulated world. "
                   "REQUIRED: Assign a 'target_node_id' if the quest involves a specific location. "
                   "Output ONLY raw JSON matching the QuestNode schema."),
        ("user", "Location: {location}\nLiving Context: {living_context}")
    ])
    
    schema_str = json.dumps(QuestNode.model_json_schema(), indent=2)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "schema": schema_str,
            "location": json.dumps(hex_context),
            "living_context": living_context
        })
        parsed = parse_json_garbage(response)
        if "step_number" not in parsed: parsed["step_number"] = 1
        return QuestNode(**parsed)
    except Exception as e:
        print(f"Mini-quest generation failed, using fallback: {e}")
        return QuestNode(
            step_number=1,
            narrative_objective=f"Investigate the anomaly at {hex_context.get('hex_id','Unknown')}.",
            trigger_location=str(hex_context.get('hex_id','Unknown')),
            encounter_type="HAZARD",
            success_state_change="REVEAL_LOOT"
        )
