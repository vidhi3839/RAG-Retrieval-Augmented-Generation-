import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ====== FIX FOR WINDOWS PATH ISSUES ======
# Set cache directory to avoid Windows path escaping issues
# This prevents the \n in usernames from being interpreted as newline
CACHE_DIR = os.path.join(os.getcwd(), "model_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Set environment variables for model caching
os.environ['TRANSFORMERS_CACHE'] = CACHE_DIR
os.environ['HF_HOME'] = CACHE_DIR
os.environ['SENTENCE_TRANSFORMERS_HOME'] = CACHE_DIR

# Paths - Use forward slashes for cross-platform compatibility
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

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


EMBEDDING_MODEL = "intfloat/e5-base-v2"
CAPTION_MODEL = "Salesforce/blip-image-captioning-large"
LLM_MODEL = "gemini-2.5-flash"

os.makedirs(BASE_DIR, exist_ok=True)
