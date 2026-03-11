import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Path relative to saga_character_engine root
CHAR_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "compiled_characters"

def save_character(player_id: str, sheet_data: Dict[str, Any]) -> bool:
    """Saves a compiled character sheet to the local filesystem."""
    try:
        os.makedirs(CHAR_DATA_DIR, exist_ok=True)
        file_path = CHAR_DATA_DIR / f"{player_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(sheet_data, f, indent=4)
        return True
    except Exception as e:
        print(f"[STORAGE] Error saving character {player_id}: {e}")
        return False

def load_character(player_id: str) -> Optional[Dict[str, Any]]:
    """Loads a compiled character sheet from the local filesystem."""
    try:
        file_path = CHAR_DATA_DIR / f"{player_id}.json"
        if not file_path.exists():
            return None
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[STORAGE] Error loading character {player_id}: {e}")
        return None
