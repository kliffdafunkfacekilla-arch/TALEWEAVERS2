from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

# The exact categories allowed in the SAGA engine
class LoreCategory(str, Enum):
    POLITICAL_FACTION = "POLITICAL_FACTION"
    CULTURE = "CULTURE"
    PLANT = "PLANT"
    ANIMAL = "ANIMAL"
    RESOURCE = "RESOURCE"
    BIOME = "BIOME"
    TECH = "TECH"
    MAGIC = "MAGIC"
    ITEM = "ITEM"
    PERSON = "PERSON"
    LOCAL_FACTION = "LOCAL_FACTION"
    HISTORY = "HISTORY"
    LORE = "LORE"

# API INPUT: /api/lore/ingest
class IngestRequest(BaseModel):
    vault_path: str = Field(..., description="Absolute local path to the Obsidian Vault")
    force_rebuild: bool = Field(default=False, description="If true, wipes the existing DB before ingest")

# API OUTPUT: /api/lore/ingest
class IngestResponse(BaseModel):
    status: str
    files_processed: int
    categories_mapped: Dict[str, int]
    errors: List[str]

# API INPUT: /api/lore/search
class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=3, description="Number of results to return")
    filter_categories: Optional[List[LoreCategory]] = Field(default=None, description="Limit search to these tags")

# API OUTPUT: /api/lore/search
class SearchResult(BaseModel):
    title: str
    category: str
    content: str
    distance: float  # The mathematical relevance score (lower is better)

class SearchResponse(BaseModel):
    results: List[SearchResult]
