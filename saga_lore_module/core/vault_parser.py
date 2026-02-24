import os
import frontmatter
from pathlib import Path
from typing import List, Dict
from .schemas import LoreCategory
from .auto_categorizer import categorize_text

def parse_vault(vault_path: str) -> List[Dict]:
    """
    Recursively find all .md files in the vault and extract content and metadata.
    """
    documents = []
    vault_root = Path(vault_path)
    
    if not vault_root.exists():
        raise FileNotFoundError(f"Vault path not found: {vault_path}")
        
    for root, _, files in os.walk(vault_root):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        post = frontmatter.load(f)
                        
                    content = post.content.strip()
                    if not content:
                        continue
                        
                    category = post.get("category")
                    if not category or category not in LoreCategory.__members__:
                        category = categorize_text(content)
                        
                    documents.append({
                        "id": str(file_path.relative_to(vault_root)),
                        "title": file_path.stem,
                        "content": content,
                        "category": str(category)
                    })
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    
    return documents
