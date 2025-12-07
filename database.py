from supabase import create_client, Client
from config import *
import os
import json

def get_dir_size_kb(directory_path):
    """Calculate directory size in KB."""
    total_size_bytes = 0
    if not os.path.exists(directory_path):
        return 0
    
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp) and not os.path.islink(fp):
                total_size_bytes += os.path.getsize(fp)
    
    return total_size_bytes / 1024

def log_document_to_db(doc_meta, num_chunks, username=None):
    """Log document metadata to Supabase with enhanced tracking."""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        doc_dirs = doc_meta["base_dir"]
        text_size = get_dir_size_kb(os.path.join(doc_dirs, "texts"))
        table_size = get_dir_size_kb(os.path.join(doc_dirs, "tables"))
        img_size = get_dir_size_kb(os.path.join(doc_dirs, "images"))
        
        doc_id_uuid = doc_meta['doc_id'] if isinstance(doc_meta['doc_id'], str) else str(doc_meta['doc_id'])
        
        payload = {
            "doc_id": doc_id_uuid,
            "filename": doc_meta['filename'],
            "doc_type": doc_meta['ext'],
            "text_size": text_size,
            "table_size": table_size,
            "img_size": img_size,
            "num_chunks": num_chunks,
            "page_count": doc_meta['text_files_count'],
            "tables_count": doc_meta['tables_count'],
            "images_count": doc_meta['images_count'],
            "uploaded_by": username
        }
        
        supabase.table("documents").insert(payload).execute()
        
        log_system_event("info", "ingestion", f"Document uploaded: {doc_meta['filename']}")
        return True
    except Exception as e:
        log_system_event("error", "ingestion", f"Failed to log document: {str(e)}")
        print(f"Database logging error: {e}")
        return False

def log_chunks_to_db(chunks):
    """Log chunks to Supabase."""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        batch = []
        for chunk in chunks:

            chunk_id_uuid = chunk["chunk_id"] if isinstance(chunk["chunk_id"], str) else str(chunk["chunk_id"])
            doc_id_uuid = chunk["doc_id"] if isinstance(chunk["doc_id"], str) else str(chunk["doc_id"])
            
            payload = {
                "chunk_id": chunk_id_uuid,
                "doc_id": doc_id_uuid,
                "type": chunk["type"],
                "page": chunk.get("page", 1),
                "content": chunk["content"],
                "embedding_generated": True
            }
            batch.append(payload)
        
        for i in range(0, len(batch), 100):
            supabase.table("chunks").insert(batch[i:i+100]).execute()
        
        return True
    except Exception as e:
        log_system_event("error", "ingestion", f"Failed to log chunks: {str(e)}")
        print(f"Chunk logging error: {e}")
        return False

def log_query_to_db(question, answer, sources, username=None, latency_ms=0, 
                    top_k=5, threshold=0.7, retrieval_success=True, error_message=None):
    """
    Log user query with comprehensive metrics.
***
    """
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Calculate metrics
        avg_similarity = sum(s.get('score', 0) for s in sources) / len(sources) if sources else 0
        

        print(f"📝 Logging query - Username: {username}, Sources count: {len(sources)}")
        
        payload = {
            "question": question,
            "answer": answer,
            "sources": json.dumps(sources),
            "top_k": top_k,
            "similarity_threshold": threshold,
            "num_sources_retrieved": len(sources),
            "query_length": len(question),
            "answer_length": len(answer),
            "latency_ms": latency_ms,
            "avg_similarity_score": avg_similarity,
            "retrieval_success": retrieval_success,
            "error_message": error_message,
            "username": username 
        }
        
        result = supabase.table("queries").insert(payload).execute()
        query_id = result.data[0]['id'] if result.data else None
        
        print(f"✅ Query logged with ID: {query_id}")
        
        # Log individual retrievals
        if query_id and sources:
            retrieval_batch = []
            for rank, source in enumerate(sources, 1):
                # *** FIX: Get doc_id from source (now included from retrieve()) ***
                doc_id = source.get('doc_id')
                chunk_id = source.get('chunk_id')
                
                # Debug logging
                print(f"   Source {rank}: chunk_id={chunk_id}, doc_id={doc_id}")
                
                retrieval_payload = {
                    "query_id": str(query_id),
                    "chunk_id": str(chunk_id) if chunk_id else None,
                    "doc_id": str(doc_id) if doc_id else None,  # ← Now properly included
                    "filename": source.get('filename'),
                    "similarity_score": float(source.get('score', 0)),
                    "rank": rank
                }
                retrieval_batch.append(retrieval_payload)
            
            if retrieval_batch:
                supabase.table("retrieval_logs").insert(retrieval_batch).execute()
                print(f"✅ Logged {len(retrieval_batch)} retrieval entries")
        
        return True
    except Exception as e:
        error_detail = f"Failed to log query: {str(e)}"
        print(f"❌ Query logging error: {error_detail}")
        log_system_event("error", "generation", error_detail)
        return False

def log_system_event(log_type, module, message, details=None):
    """Log system events for monitoring."""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        payload = {
            "log_type": log_type,
            "module": module,
            "message": message,
            "details": json.dumps(details) if details else None
        }
        
        supabase.table("system_logs").insert(payload).execute()
        return True
    except Exception as e:
        print(f"System logging error: {e}")
        return False

