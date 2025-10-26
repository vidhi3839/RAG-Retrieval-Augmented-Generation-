# RAG-AI: Knowledge-Grounded Q&A System using Retrieval-Augmented Generation

---

## Project Overview

**RAG-AI** is an intelligent **knowledge-grounded question-answering system** that combines **Retrieval-Augmented Generation (RAG)** with **Large Language Models (LLMs)** to produce accurate and context-aware responses from **custom uploaded documents**.

Unlike traditional LLMs that rely purely on internal parameters, RAG-AI retrieves relevant external information before generating answers—ensuring factual accuracy, traceability, and domain-specific understanding.

---

## Objectives

- Implement a **Retrieval-Augmented Generation (RAG)** pipeline using **FAISS** for vector-based document retrieval.  
- Generate embeddings using **Sentence-Transformers (all-MiniLM-L6-v2)**.  
- Build an **interactive Streamlit web app** for user queries and responses.  
- Design a **SQL metadata layer** to log queries, retrieved passages, responses, and latency.  
- Evaluate performance using metrics such as **retrieval accuracy**, **response relevance**, and **response latency**.  
- Visualize analytics using **SQL reports** and **Streamlit dashboards**.

---

## System Architecture

User Query  
      ↓  
Text Chunking  
      ↓  
Embedding Generation  
      ↓  
FAISS Retrieval  
      ↓  
LLM Response Generation  
      ↓  
SQL Metadata Logging (queries, latency, confidence)  
      ↓  
Streamlit Visualization & Performance Dashboard



---

## Database Design & SQL Analytics

To enhance **reproducibility and transparency**, a SQL-based metadata logging system records all interactions:

| Logged Data | Description |
|--------------|-------------|
| Query Logs | User query text & timestamps |
| Retrieval Metadata | Document IDs, similarity scores |
| Response Logs | Generated LLM responses |
| Performance Metrics | Latency, confidence, success rate |

### Example SQL Reports (8 Analytical Queries)
1. Query logs by document type or topic  
2. Most frequently retrieved documents or passages  
3. Average response latency by query length  
4. Query success rate (retrieval + response match)  
5. Embedding similarity distribution  
6. User interaction frequency by session  
7. Accuracy or confidence trends over time  
8. System error or fallback frequency report  

---

## Evaluation Metrics

| Metric | Description |
|---------|-------------|
| **Retrieval Accuracy** | % of relevant chunks retrieved |
| **Response Relevance** | Human-rated match between answer and source text |
| **Latency** | Average time per query-response cycle |

These results are **visualized in Streamlit dashboards** for clarity and performance tracking.

---

## Tools and Technologies

| Category | Tools / Libraries |
|-----------|------------------|
| Programming | Python 3.10+ |
| Retrieval & Embeddings | FAISS, Sentence-Transformers |
| LLM Integration | LangChain, OpenAI API (or similar) |
| Frontend | Streamlit |
| Database | SQL |
| Visualization | Matplotlib, Plotly, Streamlit |
| Version Control | Git & GitHub |
| Documentation | Overleaf (LaTeX) & Excel Tracker |

