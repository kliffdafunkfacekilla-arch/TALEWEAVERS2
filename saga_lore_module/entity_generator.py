import os
import glob
import json
import asyncio
from pathlib import Path
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
import sys

# Ensure core module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.vector_store import LoreVaultDB

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OSTRAKA_DIR = DATA_DIR / "Ostraka"
VAULT_DIR = OSTRAKA_DIR if OSTRAKA_DIR.exists() else DATA_DIR / "vault" / "entities"
ENTITIES_OUT_DIR = DATA_DIR / "entities"

os.makedirs(ENTITIES_OUT_DIR, exist_ok=True)

class EntityParser:
    def __init__(self):
        print("[System] Initializing Ollama (llama3) and Vector Store...")
        self.llm = Ollama(model="llama3")
        self.db = LoreVaultDB()
        
    async def process_vault(self):
        print(f"[System] Scanning vault for markdown files: {VAULT_DIR}")
        found_files = list(glob.glob(f"{VAULT_DIR}/**/*.md", recursive=True))
        if not found_files:
            print("  -> No markdown files found.")
            return

        for filepath in found_files:
            await self._process_file(filepath)
            
    async def _process_file(self, filepath):
        path = Path(filepath)
        entity_name = path.stem
        
        # The top-level folder inside the vault acts as the exact category
        try:
            rel_path = path.relative_to(VAULT_DIR)
            category = rel_path.parts[0]
        except:
            category = path.parent.name
            
        print(f"\n[Processing] Entity: '{entity_name}' (Category: {category})")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"  -> Vectorizing document into LoreDB...")
        # 1. Vectorize and store in LoreDB
        doc = {
            "id": f"entity_{category}_{entity_name.lower().replace(' ', '_')}",
            "title": entity_name,
            "content": content,
            "category": category.upper()
        }
        try:
            # We wrap it in a list as the DB expects a list of dictionaries
            self.db.add_documents([doc])
        except Exception as e:
            print(f"  -> [Warning] Vector DB skip/error: {e}")
            
        MECHANICAL_CATEGORIES = [
            "cultures", "factions and organisations", "fauna", "flora", 
            "magic and religion", "people", "resource", "tech"
        ]
        
        if category.lower() not in MECHANICAL_CATEGORIES:
            print(f"  -> [{category}] is a Narrative folder. Skipping JSON Stat generation.")
            return
            
        print(f"  -> Prompting LLM for stat block generation...")
        # 2. Extract stats using LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are the T.A.L.E.W.E.A.V.E.R. Entity Generator. Read the provided lore carefully. "
                       f"This entity belongs to the category: '{category}'. "
                       "Your job is to mathematically quantify this entity into an RPG stat block based on the lore. "
                       f"Create a custom JSON schema that perfectly fits a '{category}' type object "
                       "(e.g., if it's 'Fauna', include diet, base_health, speed. if it's 'Tech', include tech_tier, energy_cost). "
                       "Output ONLY the raw JSON object, with no markdown formatting or text outside the curly braces. DO NOT provide schemas, provide the actual data in JSON format."),
            ("user", "Entity Name: {name}\n\nLore Body:\n{content}")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "name": entity_name,
                "content": content
            })
            
            parsed = self._parse_json_garbage(response)
            
            if not parsed:
                print("  -> [Error] LLM failed to return valid JSON.")
                return

            # Save the result
            out_path = ENTITIES_OUT_DIR / category
            out_path.mkdir(exist_ok=True, parents=True) # Ensure category subfolder exists
            
            final_file = out_path / f"{entity_name.replace(' ', '_')}.json"
            with open(final_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=4)
                
            print(f"  -> [SUCCESS] Saved compiled stats: {final_file}")
            
        except Exception as e:
            print(f"  -> [ERROR] LLM Generation failed for {entity_name}: {e}")

    def _parse_json_garbage(self, text: str) -> dict:
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try: return json.loads(match.group(0))
            except Exception as e: print(f"  -> [Error] Regex JSON parsing failed: {e}")
        return {}

if __name__ == "__main__":
    parser = EntityParser()
    asyncio.run(parser.process_vault())
