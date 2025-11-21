import os

# Paths
BASE_DIR = "extracted"
DOCS_INDEX_PATH = os.path.join(BASE_DIR, "docs_index.json")
RAG_CHUNKS_PATH = os.path.join(BASE_DIR, "rag_chunks.json")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "faiss_index.faiss")
MAPPING_PATH = os.path.join(BASE_DIR, "index_mapping.json")

# Subdirectories
TEXTS_SUBDIR = "texts"
TABLES_SUBDIR = "tables"
IMAGES_SUBDIR = "images"

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Retrieval
TOP_K = 3
SIMILARITY_THRESHOLD = 0.7

# API Keys
#GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCwSoZtRlXGqb3vI2bB_rZZTJ9eZGJKHlc")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyD1Um89w6x8t-aNJO9D-hfpVLLgmgX5Ajg")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://oldmdsztelannvpymokv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9sZG1kc3p0ZWxhbm52cHltb2t2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI5NTYzOTAsImV4cCI6MjA3ODUzMjM5MH0.tzmLOKxV0XaJlVqaKVIimlnRBC8I6Gk_O7HuoLDfoyM")

# Model
EMBEDDING_MODEL = "intfloat/e5-base-v2"
CAPTION_MODEL = "Salesforce/blip-image-captioning-large"
LLM_MODEL = "gemini-2.5-flash"

# Ensure base directory exists
os.makedirs(BASE_DIR, exist_ok=True)