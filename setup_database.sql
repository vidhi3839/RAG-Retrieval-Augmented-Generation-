-- 1. Open your Supabase project
-- 2. Go to SQL Editor
-- 3. Copy and paste this entire file
-- 4. Click "Run" to create all tables

-- Table 1: Users
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Table 2: Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    username TEXT,
    session_token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_active ON sessions(is_active) WHERE is_active = TRUE;

-- Table 3: Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    doc_id UUID UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    doc_type TEXT,
    text_size FLOAT,
    table_size FLOAT,
    img_size FLOAT,
    num_chunks INT,
    page_count INT,
    tables_count INT,
    images_count INT,
    uploaded_by TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_doc_id ON documents(doc_id);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);

-- Table 4: Chunks
CREATE TABLE IF NOT EXISTS chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chunk_id UUID UNIQUE NOT NULL,
    doc_id UUID REFERENCES documents(doc_id) ON DELETE CASCADE,
    type TEXT,
    page INT,
    content TEXT,
    embedding_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_chunk_id ON chunks(chunk_id);
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_chunks_type ON chunks(type);

-- Table 5: Queries
CREATE TABLE IF NOT EXISTS queries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT,
    sources JSONB,
    username TEXT,
    top_k INT,
    similarity_threshold FLOAT,
    num_sources_retrieved INT,
    query_length INT,
    answer_length INT,
    latency_ms FLOAT,
    avg_similarity_score FLOAT,
    retrieval_success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_queries_username ON queries(username);
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_queries_retrieval_success ON queries(retrieval_success);

-- Table 6: Retrieval Logs
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    query_id UUID REFERENCES queries(id) ON DELETE CASCADE,
    chunk_id UUID,
    doc_id UUID,
    filename TEXT,
    similarity_score FLOAT,
    rank INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_retrieval_logs_query_id ON retrieval_logs(query_id);
CREATE INDEX idx_retrieval_logs_doc_id ON retrieval_logs(doc_id);
CREATE INDEX idx_retrieval_logs_chunk_id ON retrieval_logs(chunk_id);

-- Table 7: System Logs
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    log_type TEXT NOT NULL,
    module TEXT,
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_system_logs_type ON system_logs(log_type);
CREATE INDEX idx_system_logs_module ON system_logs(module);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
