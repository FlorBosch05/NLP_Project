"""Build and query a local recipe index."""
import json
import os
from pathlib import Path
import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

ROOT = Path(__file__).resolve().parent.parent

def build_index():
    recipes = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
    documents = []
    for recipe in recipes:
        common = {"recipe": recipe["name"], "servings": recipe["servings"]}
        for section in ("overview", "ingredients", "instructions", "dietary_tags"):
            value = recipe[section]
            text = json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value
            documents.append(Document(text=f"Recipe: {recipe['name']}\n{section}: {text}", metadata={**common, "section": section}))
    client = chromadb.PersistentClient(path=str(ROOT / "storage" / "chroma"))
    # Rebuild the collection to prevent duplicate entries on repeated starts.
    if any(collection.name == "recipes" for collection in client.list_collections()):
        client.delete_collection("recipes")
    collection = client.get_or_create_collection("recipes")
    store = ChromaVectorStore(chroma_collection=collection)
    embedding = HuggingFaceEmbedding(model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"), cache_folder=str(ROOT / "storage" / "models"))
    return VectorStoreIndex.from_documents(documents, storage_context=StorageContext.from_defaults(vector_store=store), embed_model=embedding)
