import os
import frontmatter
from pathlib import Path
from typing import List, Dict
from .lore_schemas import LoreCategory
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
                        
                    # Be forgiving: Check if user wrote 'category' or 'type' in their Markdown
                    raw_category = post.get("category") or post.get("type")
                    category = None
                    
                    # Try to map their string to our strict Enum
                    if raw_category:
                        raw_upper = str(raw_category).upper().replace(" ", "_")
                        if raw_upper in LoreCategory.__members__:
                            category = LoreCategory[raw_upper]
                            
                    # If no valid frontmatter exists, use our new smart categorizer and pass the relative file path!
                    if not category:
                        category = categorize_text(content, str(file_path.relative_to(vault_root)))
                        
                    documents.append({
                        "id": str(file_path.relative_to(vault_root)),
                        "title": file_path.stem,
                        "content": content,
                        "category": str(category)
                    })
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    
    return documents
