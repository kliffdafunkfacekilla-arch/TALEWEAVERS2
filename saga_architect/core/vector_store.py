import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import os
import shutil
from pathlib import Path

# Step up to the root project directory and find the master data folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class LoreVaultDB:
    def __init__(self, db_path=str(DATA_DIR / "lore" / ".chroma")):
        """
        Initialize persistent local storage with local sentence-transformers.
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Local model: sentence-transformers/all-MiniLM-L6-v2
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="saga_lore",
            embedding_function=self.embed_fn
        )

    def wipe_db(self):
        """
        Deletes the physical database folder content.
        """
        try:
            self.client.delete_collection("saga_lore")
        except:
            pass
        self.collection = self.client.get_or_create_collection(
            name="saga_lore",
            embedding_function=self.embed_fn
        )

    def add_documents(self, documents: List[Dict]):
        """
        Inests a list of document dicts into the vector store.
        documents = [{"id": "...", "content": "...", "category": "...", "title": "..."}]
        """
        ids = [doc["id"] for doc in documents]
        contents = [doc["content"] for doc in documents]
        metadatas = [{"category": doc["category"], "title": doc["title"]} for doc in documents]
        
        self.collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )

    def query(self, query_text: str, top_k: int = 3, filter_categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Natural language search with optional metadata filtering.
        """
        where_clause = {}
        if filter_categories:
            if len(filter_categories) == 1:
                where_clause = {"category": filter_categories[0]}
            else:
                where_clause = {"category": {"$in": filter_categories}}
                
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        
        # Format results for the API
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "title": results["metadatas"][0][i]["title"],
                    "category": results["metadatas"][0][i]["category"],
                    "content": results["documents"][0][i],
                    "distance": float(results["distances"][0][i])
                })
                
        return formatted_results
