import json
import os
import re
import httpx
from typing import List, Optional
from core.weaver_schemas import CampaignRoadmap, QuestNode, CampaignFramework, StoryArcStage
from langchain_ollama import OllamaLLM as Ollama
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
        except Exception as e:
            print(f"[Weaver Error] Failed to load MAP_FILE: {e}")
    return {"world_name": "Shatterlands", "regions": [], "macro_map": []}

def normalize_framework_data(data: dict) -> dict:
    # Handle top-level keys
    if "hero_journey" not in data:
        for k in ["journey", "stages", "beats", "arc"]:
            if k in data:
                data["hero_journey"] = data[k]
                break

    if "hero_journey" in data and isinstance(data["hero_journey"], list):
        for stage in data["hero_journey"]:
            # stage_name normalization
            if "stage_name" not in stage:
                for nk in ["stage", "name", "stage_title", "step"]:
                    if nk in stage:
                        stage["stage_name"] = stage[nk]
                        break
            # narrative_objective normalization
            if "narrative_objective" not in stage:
                for ok in ["objective", "goal", "task", "mission"]:
                    if ok in stage:
                        stage["narrative_objective"] = stage[ok]
                        break
            # plot_point normalization
            if "plot_point" not in stage:
                for pk in ["point", "event", "story_beat"]:
                    if pk in stage:
                        stage["plot_point"] = stage[pk]
                        break
            # foreshadowing_clue normalization
            if "foreshadowing_clue" not in stage:
                for fk in ["clue", "hint", "foreshadowing"]:
                    if fk in stage:
                        stage["foreshadowing_clue"] = stage[fk]
                        break
            if "pacing_milestones" not in stage: stage["pacing_milestones"] = 2
    
    # character_hooks normalization (Ollama often sends objects instead of strings)
    if "character_hooks" in data and isinstance(data["character_hooks"], list):
        normalized_hooks = []
        for hook in data["character_hooks"]:
            if isinstance(hook, dict):
                # Flatten dict to string: "Name: Hook"
                h_name = hook.get("name") or hook.get("character") or "Player"
                h_text = hook.get("hook") or hook.get("description") or str(hook)
                normalized_hooks.append(f"{h_name}: {h_text}")
            else:
                normalized_hooks.append(str(hook))
        data["character_hooks"] = normalized_hooks
        
    return data

def parse_json_garbage(text: str) -> dict:
    text = text.strip()
    # Find the outermost { }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except: pass
    return {}

async def generate_campaign_framework(characters: List[dict], world_state: dict, settings: dict, history: Optional[List[dict]] = None, context_packet: Optional[dict] = None) -> CampaignFramework:
    """Generates or adjusts a full 8-stage Hero's Journey arc."""
    llm = Ollama(model="llama3")
    
    # LOAD FULL WORLD SIM DATA FOR LOGIC
    full_world = await fetch_world_data()
    # Filter to essential story-driving data
    world_logic_context = {
        "world_name": full_world.get("world_name"),
        "active_factions": full_world.get("factions", []),
        "recent_history": full_world.get("world_events", [])[:10],
        "starting_hex_details": world_state.get("starting_hex")
    }
    
    length_setting = settings.get("length", "SAGA")
    pacing_instruction = "between 2 to 3"
    if length_setting == "ONE_SHOT": pacing_instruction = "exactly 1"
    elif length_setting == "EPIC": pacing_instruction = "between 4 to 6"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver (Mode: LOGIC-FIRST). "
                   "1. LOGIC: Identify a specific conflict involving the Factions or History provided. "
                   "2. FRAME: Create an 8-beat Hero's Journey that logically resolves or intervenes in that conflict. "
                   "3. Output ONLY valid JSON. No metaphors. No 'whispers in the wind'."),
        ("user", "WORLD SIM DATA: {world_logic}\nCHARACTERS: {characters}\nSETTINGS: {settings}\n\n"
                 "REQUIRED JSON FIELDS: arc_name, theme, hero_journey (list of 8: stage_name, plot_point, narrative_objective, foreshadowing_clue), character_hooks\n"
                 "Output raw JSON:")
    ])
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "world_logic": json.dumps(world_logic_context),
            "characters": json.dumps(characters),
            "settings": json.dumps(settings)
        })
        raw_data = parse_json_garbage(response)
        parsed = normalize_framework_data(raw_data)
        
        # Repair common omissions
        if "hero_journey" in parsed:
            if "arc_name" not in parsed: parsed["arc_name"] = "A Procedural Saga"
            if "theme" not in parsed: parsed["theme"] = settings.get("style", "Survival")
            if "character_hooks" not in parsed: parsed["character_hooks"] = []
            return CampaignFramework(**parsed)
        
        raise ValueError("JSON missing hero_journey")
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
    except Exception as e:
        print(f"[Weaver Error] Regional Arc generation failed: {e}")
        return []

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

async def generate_tactical_errand(location: str) -> QuestNode:
    """Tier 4: Generates a short tactical errand (e.g., fetch, scout, clear)."""
    llm = Ollama(model="llama3")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the T.A.L.E.W.E.A.V.E.R. Campaign Weaver (Tier: ERRAND). "
                   "Generate a short tactical objective for a building or small area. "
                   "Output ONLY raw JSON matching the QuestNode schema."),
        ("user", "Location: {location}")
    ])
    
    try:
        response = await (prompt | llm).ainvoke({"location": location})
        parsed = parse_json_garbage(response)
        if "step_number" not in parsed: parsed["step_number"] = 1
        return QuestNode(**parsed)
    except Exception as e:
        print(f"[Weaver Error] Tactical Errand generation failed: {e}")
        return QuestNode(
            step_number=1,
            narrative_objective=f"Secure the perimeter at {location}.",
            trigger_location=location,
            encounter_type="COMBAT",
            success_state_change="COMPLETE"
        )
