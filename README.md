# RAG-AI: Knowledge-Grounded Q&A System using Retrieval-Augmented Generation

---

## 1. Project Goal

The goal of this project is to build a **Retrieval-Augmented Generation (RAG) system** that allows users to upload documents and ask natural language questions about them. The system retrieves relevant information from the documents and generates accurate, context-based answers using a Large Language Model (LLM).

**Key Features:**
- Multi-format document support (PDF, DOCX, TXT, CSV)
- User authentication and session management
- Semantic search using FAISS vector database
- Context-aware answer generation using Google Gemini
- Admin analytics dashboard for performance monitoring
- Source attribution for transparency

---

## 2. How to Run the Code

### Prerequisites
- Python 3.8 or higher
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Supabase account ([Sign up here](https://supabase.com))

### Step 1: Clone the Repository
```bash
git clone (https://github.com/vidhi3839/RAG-Retrieval-Augmented-Generation-.git)
```

### Step 2: Install Dependencies
```bash
# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 3: Set Up Database
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** from the left sidebar
3. Open the `setup_database.sql` file from this repository
4. Copy the entire SQL script and paste it into the SQL Editor
5. Click **"Run"** to create all tables and indexes
6. Verify tables were created in the **Table Editor**

   
### Step 4: Set Up Environment Variables
Create a `.env` file in the project root directory:
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### Step 5: Run the Application
```bash
streamlit run app.py
```

The application will open in your browser

### Step 6: First Time Usage
1. **Register an Account:** Click "Sign up", enter username and password
2. **Upload a Document:** Use the upload interface to add your first document (PDF, DOCX, TXT, or CSV)
3. **Wait for Processing:** The system will extract text and create embeddings
4. **Ask Questions:** Type questions in the text box and get answers with source citations

---

## 3. Requirements and Dependencies

### Python Dependencies
```txt
streamlit==1.31.0
transformers==4.36.0
torch==2.1.0
sentence-transformers==2.3.1
faiss-cpu==1.7.4
pymupdf==1.23.8
pdfplumber==0.10.3
pytesseract==0.3.10
pillow==10.1.0
python-docx==1.1.0
markdown==3.5.1
beautifulsoup4==4.12.2
openpyxl==3.1.2
pandas==2.1.4
numpy==1.26.2
google-generativeai==0.3.2
supabase==2.3.0
python-dotenv==1.0.0
```

All dependencies are listed in `requirements.txt` and can be installed with:
```bash
pip install -r requirements.txt
```

### External Services
1. **Google Gemini API** - For answer generation (LLM)
2. **Supabase** - For user authentication and data storage

---

## 4. Approach and Methodology

### System Architecture

Our RAG system consists of five main components:

#### 4.1 Document Ingestion (`ingestion.py`)
- **Purpose:** Process uploaded documents and extract text
- **Formats Supported:** PDF, DOCX, TXT, CSV
- **Chunking Strategy:** 
  - Chunk Size: 500 tokens
  - Overlap: 100 tokens
- **Metadata Tracking:** Filename, page numbers, document type, upload timestamp

#### 4.2 Embedding & Indexing (`retrieval.py`)
- **Embedding Model:** `intfloat/e5-base-v2` (768-dimensional embeddings)
- **Vector Database:** FAISS with HNSW index for fast similarity search
- **Index Type:** `IndexHNSWFlat` with inner product (cosine similarity)
- **Incremental Indexing:** New documents are added without rebuilding the entire index

#### 4.3 Retrieval System (`retrieval.py`)
- **Query Processing:** User questions are embedded using the same e5-base-v2 model
- **Similarity Search:** FAISS returns top-k most similar chunks (default k=3)
- **Threshold Filtering:** Only chunks with similarity score > 0.7 are used
- **Result Ranking:** Results ranked by cosine similarity score

#### 4.4 Answer Generation (`generation.py`)
- **LLM:** Google Gemini 2.5 Flash
- **Prompt Engineering:** Instructs model to answer ONLY from provided context
- **Temperature:** 0.2 (for consistent, factual responses)
- **Fallback:** Returns "Not available in the provided notes" when no relevant context is found

#### 4.5 User Authentication (`auth_db.py`)
- **Password Security:** SHA-256 hashing
- **Session Management:** 7-day session expiry with token-based authentication
- **Database:** Supabase (PostgreSQL) for user accounts and sessions

### RAG Pipeline Flow

```
User Question
    ↓
Query Embedding (e5-base-v2)
    ↓
FAISS Vector Search (top-k chunks)
    ↓
Similarity Filtering (threshold > 0.7)
    ↓
Context Assembly
    ↓
Gemini LLM Generation
    ↓
Answer + Source Citations
```

### Database Schema

The system uses 7 tables in Supabase:

1. **users** - User accounts and credentials
2. **sessions** - Active user sessions
3. **documents** - Uploaded document metadata
4. **chunks** - Text chunks with embeddings
5. **queries** - Query history and performance metrics
6. **retrieval_logs** - Detailed retrieval tracking
7. **system_logs** - System events and errors

All tables are created by running `setup_database.sql`.

### Key Configuration Parameters

Located in `config.py`:
```python
CHUNK_SIZE = 500              # Tokens per chunk
CHUNK_OVERLAP = 100           # Overlap between chunks
TOP_K = 3                     # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.7    # Minimum similarity score
EMBEDDING_MODEL = "intfloat/e5-base-v2"
LLM_MODEL = "gemini-2.5-flash"
```

---

## 5. Results and Outputs

### System Capabilities

**Successfully Implemented:**
Multi-format document upload and processing  
Semantic search with FAISS vector database  
Accurate answer generation from context  
User authentication and session management  
Real-time performance tracking  
Admin analytics dashboard  


### Performance Metrics

The system tracks the following metrics for each query:
- **Latency:** Time from question submission to answer (typically 1-2 seconds)
- **Retrieval Success Rate:** Percentage of queries where relevant context was found
- **Similarity Scores:** Cosine similarity of retrieved chunks
- **Answer Quality:** Monitored through admin dashboard

### Admin Analytics Dashboard

The admin dashboard provides 8 SQL-based analytics queries:

1. **Total Documents & Storage** - Overall system usage
2. **Average Query Performance** - Response time metrics
3. **Most Queried Documents** - Popular documents
4. **User Activity Tracking** - Queries per user
5. **Retrieval Quality Metrics** - Average similarity scores
6. **Error Rate Monitoring** - Failed queries
7. **Document Statistics** - Chunks per document
8. **System Health** - Recent activity logs

### Screenshots

#### Main Interface
<img width="1919" height="854" alt="signup" src="https://github.com/user-attachments/assets/6d83123a-40e5-42e0-8cf6-f7a96bdece20" />

<img width="1914" height="819" alt="user_query" src="https://github.com/user-attachments/assets/9aaad8e5-e3f0-4639-ab50-20133d7bad30" />

<img width="1917" height="788" alt="upload_history" src="https://github.com/user-attachments/assets/d48491b8-f7cc-45f5-ad98-868f8dfc20dd" />

#### Admin Dashboard
*Comprehensive system analytics and performance metrics*

<img width="1546" height="858" alt="sql_query1" src="https://github.com/user-attachments/assets/6ba44d6d-dab5-48a7-bf80-5f064693cc23" />

<img width="1559" height="863" alt="sql_query2" src="https://github.com/user-attachments/assets/aad652d6-6561-4e17-ae40-03b42ad70492" />

<img width="1560" height="854" alt="sql_query3" src="https://github.com/user-attachments/assets/966770c4-aaab-4eed-9427-f67cfe0a2622" />

<img width="1607" height="860" alt="sql_query4" src="https://github.com/user-attachments/assets/9979fbdf-7991-4073-936d-ecb994f577aa" />

<img width="1582" height="453" alt="sql_query5" src="https://github.com/user-attachments/assets/87c9e7b3-5fa3-4263-a670-ec01bb475c12" />

<img width="1613" height="848" alt="sql_query6" src="https://github.com/user-attachments/assets/551ea758-df5e-4be1-a235-0a4dc79cc94e" />

<img width="1591" height="699" alt="sql_query7" src="https://github.com/user-attachments/assets/e336e6e6-6707-49d8-9e17-89d8e9ee8ce8" />

<img width="1592" height="241" alt="sql_query8" src="https://github.com/user-attachments/assets/e506a90a-0110-4e20-9873-1c5ea1bab838" />

---

## 6. File Structure

```
RAG-Retrieval-Augmented-Generation-/
│
├── app.py                   # Main Streamlit application
├── config.py                # Configuration settings
├── auth_db.py               # User authentication logic
├── database.py              # Database operations
├── ingestion.py             # Document processing
├── retrieval.py             # FAISS indexing and search
├── generation.py            # LLM answer generation
├── admin_analytics.py       # Admin dashboard queries
│
├── setup_database.sql       # Database schema (run on Supabase)
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## 7. Code Organization

All code files are well-commented and organized by functionality:

- **`app.py`** - Streamlit UI with three pages: Login/Register, Main Q&A, Admin Analytics
- **`ingestion.py`** - Document parsing with support for PDF, DOCX, TXT, CSV
- **`retrieval.py`** - FAISS vector database operations and semantic search
- **`generation.py`** - RAG pipeline integration with Gemini LLM
- **`auth_db.py`** - Secure authentication with session management
- **`database.py`** - Comprehensive logging to Supabase
- **`admin_analytics.py`** - SQL queries for system monitoring

Each module has clear docstrings and inline comments explaining the logic.

---
