import google.generativeai as genai
from config import *
import time

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

print("API", GOOGLE_API_KEY)

PROMPT_TEMPLATE = """
You are a highly factual research assistant.

Use ONLY the information provided in the context below to answer the question.
If the answer is not clearly mentioned, respond exactly with:
"Not available in the provided notes."

---
Context:
{context}
---
Question:
{question}

Give a clear, concise, and context-based answer. Do not use external knowledge.
"""

def generate_answer(question, context_chunks, model_name=LLM_MODEL):
    """Generate answer using Gemini with retrieved context."""
    context_text = "\n\n".join([chunk["content"] for chunk in context_chunks])
    prompt = PROMPT_TEMPLATE.format(context=context_text, question=question)
    
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 1024,
        }
    )
    print(response)
    return response.text.strip()

def rag_pipeline(question, chunks, top_k=TOP_K, threshold=SIMILARITY_THRESHOLD, username=None, user_doc_ids=None):
    """
    Complete RAG pipeline with timing and logging.
    
    latency_ms = Response time in milliseconds (performance metric)
    username = Current logged-in user
    user_doc_ids = Set of doc_ids belonging to the user (for filtering)
    """
    from retrieval import retrieve
    from database import log_query_to_db
    
    start_time = time.time()
    
    try:
        # Retrieval phase
        retrieval = retrieve(query=question, chunks=chunks, top_k=top_k, threshold=threshold, user_doc_ids=user_doc_ids)
        
        if retrieval["answer"] == "Not available" or len(retrieval["evidence"]) == 0:
            latency_ms = (time.time() - start_time) * 1000
            log_query_to_db(
                question, 
                "Not available in the provided notes.", 
                [], 
                username=username,
                latency_ms=latency_ms,
                top_k=top_k,
                threshold=threshold,
                retrieval_success=False
            )
            return {
                "answer": "Not available in the provided notes.", 
                "sources": [], 
                "latency_ms": latency_ms
            }
        
        # Generation phase
        final_answer = generate_answer(question, retrieval["evidence"])
        
        latency_ms = (time.time() - start_time) * 1000
        
        sources = retrieval["evidence"]
        
        # Log to database
        log_query_to_db(
            question, 
            final_answer, 
            sources,
            username=username,
            latency_ms=latency_ms,
            top_k=top_k,
            threshold=threshold,
            retrieval_success=True
        )
        
        return {
            "answer": final_answer, 
            "sources": sources,
            "latency_ms": latency_ms
        }
    
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        log_query_to_db(
            question, 
            f"Error: {error_msg}", 
            [],
            username=username,
            latency_ms=latency_ms,
            top_k=top_k,
            threshold=threshold,
            retrieval_success=False,
            error_message=error_msg
        )
        return {
            "answer": f"An error occurred: {error_msg}",
            "sources": [],
            "latency_ms": latency_ms
        }
