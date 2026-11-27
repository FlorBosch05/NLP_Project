"""Index the curated recipe corpus using selectable chunking strategies."""
import hashlib
import json
import os
from pathlib import Path
import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent

def read_recipes():
    return json.loads((ROOT / "data" / "recipes_v2.json").read_text(encoding="utf-8"))

def make_documents(strategy="sections"):
    if strategy not in {"sections", "recipe"}:
        raise ValueError("Choose sections or recipe")
    docs = []
    for r in read_recipes():
        sections = {
            "overview": f"{r['overview']} Serves {r['servings']}.",
            "ingredients": json.dumps(r["ingredients"], ensure_ascii=False),
            "instructions": r["instructions"],
            "dietary": f"Tags: {', '.join(r['dietary_tags'])}. {r['dietary_note']}",
        }
        if strategy == "recipe":
            sections = {"recipe": "\n".join(f"{k}: {v}" for k, v in sections.items())}
        for section, body in sections.items():
            metadata = {"recipe": r["name"], "section": section, "servings": r["servings"], "source": r["source"]}
            docs.append(Document(text=f"Recipe: {r['name']}\n{section}: {body}", metadata=metadata))
    return docs

def build_index(strategy="sections", rebuild=False):
    docs = make_documents(strategy)
    fingerprint = hashlib.sha256((json.dumps(read_recipes(), sort_keys=True) + strategy + os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")).encode()).hexdigest()[:12]
    name = f"recipes_{strategy}_{fingerprint}"
    client = chromadb.PersistentClient(path=str(ROOT / "storage" / "chroma"))
    existing = {c.name for c in client.list_collections()}
    if rebuild and name in existing:
        client.delete_collection(name)
        existing.remove(name)
    collection = client.get_or_create_collection(name)
    store = ChromaVectorStore(chroma_collection=collection)
    embed = HuggingFaceEmbedding(model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"), cache_folder=str(PARENT / "storage" / "models"))
    if name in existing and collection.count():
        return VectorStoreIndex.from_vector_store(store, embed_model=embed)
    return VectorStoreIndex.from_documents(docs, storage_context=StorageContext.from_defaults(vector_store=store), embed_model=embed)
