import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import *
import os

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model

# INCREMENTAL FAISS INDEX (KEY FIX) 
def build_faiss_index(chunks, append=True):
    """
    Build or append to FAISS index.
    append=True: Add to existing index (for multiple uploads)
    append=False: Rebuild from scratch
    """
    model = get_embedding_model()
    
    # Load existing index if appending
    if append and os.path.exists(FAISS_INDEX_PATH) and os.path.exists(MAPPING_PATH):
        print("Loading existing FAISS index...")
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            existing_chunk_ids = json.load(f)
    else:
        print("Creating new FAISS index...")
        index = None
        existing_chunk_ids = []
    
    texts = [c["content"] for c in chunks]
    chunk_ids = [c["chunk_id"] for c in chunks]
    
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,  
        batch_size=32  
    )
    embeddings = embeddings.astype('float32')
    
    # Create or append to index
    d = embeddings.shape[1]
    if index is None:
        index = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
    
    # Add new embeddings
    index.add(embeddings)
    
    # Combine chunk IDs
    all_chunk_ids = existing_chunk_ids + chunk_ids
    
    # Save index and mapping
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunk_ids, f)
    
    print(f"✅ FAISS index updated: {index.ntotal} total vectors")
    return index, all_chunk_ids

def load_faiss_index():
    """Load existing FAISS index and mapping."""
    try:
        if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(MAPPING_PATH):
            print("FAISS index files not found")
            return None, None
        
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            index_mapping = json.load(f)
        
        print(f"✅ Loaded FAISS index with {index.ntotal} vectors")
        return index, index_mapping
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None, None

def retrieve(query, chunks, top_k=TOP_K, threshold=SIMILARITY_THRESHOLD, user_doc_ids=None):
    """
    Retrieve relevant chunks for a query.
    user_doc_ids: Ignored - we search all documents
    """
    index, index_mapping = load_faiss_index()
    
    if index is None:
        return {"answer": "Not available", "evidence": []}
    
    # Build chunk lookup from ALL chunks
    chunk_lookup = {c["chunk_id"]: c for c in chunks}
    
    # Embed query
    model = get_embedding_model()
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype('float32')
    
    # Search
    D, I = index.search(q_emb, top_k)
    
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(index_mapping):
            continue
        chunk_id = index_mapping[idx]
        if chunk_id not in chunk_lookup:
            continue
        meta = chunk_lookup[chunk_id]
        
        # NO USER FILTERING - include all results
        results.append({
            "chunk_id": chunk_id,
            "doc_id": meta.get("doc_id"),
            "score": float(score),
            "content": meta["content"],
            "filename": meta.get("filename"),
            "page": meta.get("page"),
            "type": meta.get("type"),
            "caption": meta.get("caption", "")
        })
    
    # Check threshold
    if len(results) == 0 or results[0]["score"] < threshold:
        return {"answer": "Not available", "evidence": []}
    
    return {"answer": None, "evidence": results}
