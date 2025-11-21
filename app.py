import streamlit as st
import json
import os
from pathlib import Path
import traceback

# Import your modules with error handling
try:
    from ingestion import ingest_file, save_index_and_chunks
    from retrieval import build_faiss_index, load_faiss_index
    from generation import rag_pipeline
    from database import log_document_to_db, log_chunks_to_db
    from config import *
    from auth_db import create_user, verify_user, create_session, validate_session, logout_session
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# --- Page Config ---
st.set_page_config(
    page_title="RAG Intelligence System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize all session state variables."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False
    if "docs_index" not in st.session_state:
        st.session_state.docs_index = []
    if "all_docs" not in st.session_state:
        st.session_state.all_docs = []
    if "chunks" not in st.session_state:
        st.session_state.chunks = []
    if "faiss_ready" not in st.session_state:
        st.session_state.faiss_ready = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Validate existing session on page load
    if st.session_state.session_token:
        try:
            validation = validate_session(st.session_state.session_token)
            if not validation["valid"]:
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.session_token = None
        except Exception as e:
            print(f"Session validation error: {e}")
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.session_token = None

# --- Custom CSS - Soft Blue Theme ---
def load_css():
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 0rem !important;}
    
    .stApp {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stTextInput {
        margin-bottom: 0px !important;
    }
    
    .stTextInput input {
        border: 2px solid #e3f2fd !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        background: #f8fbff !important;
        height: 35px !important;
        color: #000000 !important;
    }
    
    .stTextInput input:focus {
        border-color: #64b5f6 !important;
        box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.1) !important;
    }
    
    .stTextInput label {
        font-size: 12px !important;
        font-weight: 500 !important;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #64b5f6 0%, #42a5f5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        width: 30% !important;
        height: 36px !important;
        margin-right: 0px;
        margin-left: 40%;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(100, 181, 246, 0.4) !important;
    }
    
    .card {
        background: white;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(100, 149, 237, 0.1);
        margin: 15px 0;
    }
    
    .answer-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 25px;
        border-radius: 15px;
        border-left: 5px solid #42a5f5;
        margin: 15px 0;
        color: #1565c0;
        font-size: 16px;
        line-height: 1.8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Login/Signup Page ---
def show_auth_page():
    st.markdown("<br>", unsafe_allow_html=True)
    
    left_col, right_col = st.columns([1, 1], gap="medium")
    
    with left_col:
        st.markdown('<div style="padding: 35px 30px; border-radius: 18px;">', unsafe_allow_html=True)
        
        st.markdown('<h1 style="color: #1976d2; text-align: center; margin-bottom: 6px; font-size: 36px;">Login</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #64b5f6; text-align: center; margin-bottom: 25px; font-size: 25px;">RAG Intelligence System</p>', unsafe_allow_html=True)
        
        if st.session_state.show_signup:
            st.markdown("### Create Account")
            username = st.text_input("Username", key="signup_username", placeholder="Enter username")
            st.markdown("<div style='margin: 5px 0;'></div>", unsafe_allow_html=True)
            password = st.text_input("Password", type="password", key="signup_password", placeholder="Enter password")
            
            st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
            
            if st.button("Sign Up", use_container_width=True, key="signup_btn"):
                if username == "" or password == "":
                    st.warning("⚠️ Please fill all fields")
                else:
                    result = create_user(username, password)
                    if result["success"]:
                        st.success("✅ Account created!")
                        st.session_state.show_signup = False
                        st.rerun()
                    else:
                        st.error(f"❌ {result['error']}")
            
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
            
            # Text link for back to login
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.markdown("<p style='text-align: center; color: #90a4ae; font-size: 13px; margin-bottom: 5px;'>Have an account?</p>", unsafe_allow_html=True)
                if st.button("Back to Login", key="back_login", use_container_width=True):
                    st.session_state.show_signup = False
                    st.rerun()
        
        else:
            # Email field with inline label
            col_label1, col_input1 = st.columns([1, 3])
            with col_label1:
                st.markdown("<div style='padding-top: 8px;'><label style='font-size: 20px; font-weight: 500; color: #000;'>Email</label></div>", unsafe_allow_html=True)
            with col_input1:
                username = st.text_input("Email", key="login_username", placeholder="example@email.com", label_visibility="collapsed")
            
            st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
            
            # Password field with inline label
            col_label2, col_input2 = st.columns([1, 3])
            with col_label2:
                st.markdown("<div style='padding-top: 8px;'><label style='font-size: 20px; font-weight: 500; color: #000;'>Password</label></div>", unsafe_allow_html=True)
            with col_input2:
                password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password", label_visibility="collapsed")
            
            st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)
            
            if st.button("Login", use_container_width=True, key="login_btn"):
                if username == "" or password == "":
                    st.warning("⚠️ Please fill all fields")
                else:
                    result = verify_user(username, password)
                    if result["success"]:
                        user = result["user"]
                        session_result = create_session(user["id"], username)
                        
                        if session_result["success"]:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.session_token = session_result["token"]
                            st.success(f"✅ Welcome!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create session")
                    else:
                        st.error(f"❌ {result['error']}")
            
            st.markdown("<div style='margin: 18px 0;'></div>", unsafe_allow_html=True)
            
            # Text link for signup
            st.markdown("""
            <div style='text-align: center;'>
                <span style='color: #90a4ae; font-size: 13px;'>Don't have an account? </span>
                <span key='signup_trigger_hidden' style='color: #42a5f5; font-weight: 600; font-size: 13px; cursor: pointer; text-decoration: underline;'>Sign Up</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden button for signup trigger - using markdown to hide it
            st.markdown("<div style='height: 0; overflow: hidden;'>", unsafe_allow_html=True)
            if st.button("signup", key="signup_trigger_hidden"):
                st.session_state.show_signup = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Container with glassmorphism
        
        st.markdown("<h2 style='color: #1976d2; text-align: center; margin-bottom: 25px; font-size: 30px;'>⚡ How RAG Works</h2>", unsafe_allow_html=True)
        
        # 2x2 Grid of cards
        st.markdown("""
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;'>
            <div style='background: white; padding: 15px; border-radius: 12px; box-shadow: 0 8px 20px rgba(100, 181, 246, 0.25); border-top: 3px solid #64b5f6; text-align: center; transition: transform 0.3s ease;'>
                <div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 10px;'>📄</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 16px; margin-bottom: 4px;'>1. Upload</div>
                <div style='color: #64b5f6; font-size: 14px;'>Documents</div>
            </div>
            <div style='background: white; padding: 15px; border-radius: 12px; box-shadow: 0 8px 20px rgba(66, 165, 245, 0.25); border-top: 3px solid #42a5f5; text-align: center; transition: transform 0.3s ease;'>
                <div style='background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%); width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin: 0 auto 10px;'>⚡</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 16px; margin-bottom: 4px;'>2. Embeddings</div>
                <div style='color: #64b5f6; font-size: 14px;'>Vectorize</div>
            </div>
        </div>
        
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
            <div style='background: white; padding: 15px; border-radius: 12px; box-shadow: 0 8px 20px rgba(66, 165, 245, 0.25); border-top: 3px solid #1e88e5; text-align: center; transition: transform 0.3s ease;'>
                <div style='background: linear-gradient(135deg, #90caf9 0%, #42a5f5 100%); width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 10px;'>🔍</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 16px; margin-bottom: 4px;'>3. Search</div>
                <div style='color: #64b5f6; font-size: 14px;'>FAISS Index</div>
            </div>
            <div style='background: white; padding: 15px; border-radius: 12px; box-shadow: 0 8px 20px rgba(25, 118, 210, 0.25); border-top: 3px solid #1976d2; text-align: center; transition: transform 0.3s ease;'>
                <div style='background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%); width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: white; margin: 0 auto 10px;'>🤖</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 16px; margin-bottom: 4px;'>4. Generate</div>
                <div style='color: #64b5f6; font-size: 14px;'>AI Answer</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Bottom text
        st.markdown("""
        <div style='text-align: center; margin-top: 25px; padding-top: 20px; border-top: 2px solid rgba(100, 181, 246, 0.2);'>
            <div style='color: #1976d2; font-weight: 600; font-size: 26px; margin-bottom: 6px;'>Retrieval-Augmented Generation</div>
            <div style='color: #14b5b2; font-size: 24px;'>Smart answers from your documents</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


# --- Load Existing Data ---
def load_existing_data():
    """Load all documents and chunks. Filter only for library display."""
    try:
        if os.path.exists(DOCS_INDEX_PATH):
            with open(DOCS_INDEX_PATH, "r") as f:
                all_docs = json.load(f)
                st.session_state.all_docs = all_docs
                
                if st.session_state.username:
                    st.session_state.docs_index = [
                        doc for doc in all_docs 
                        if doc.get('uploaded_by') == st.session_state.username
                    ]
                    print(f"📚 User {st.session_state.username} sees {len(st.session_state.docs_index)} of {len(all_docs)} total documents in Library")
                else:
                    st.session_state.docs_index = all_docs
        
        if os.path.exists(RAG_CHUNKS_PATH):
            with open(RAG_CHUNKS_PATH, "r") as f:
                st.session_state.chunks = json.load(f)
            print(f"🔍 {len(st.session_state.chunks)} total chunks available for querying")
        
        try:
            index, mapping = load_faiss_index()
            if index is not None:
                st.session_state.faiss_ready = True
                print(f"✅ FAISS index loaded with {index.ntotal} vectors")
            else:
                st.session_state.faiss_ready = False
                print("⚠️ No FAISS index found")
        except Exception as e:
            print(f"⚠️ FAISS index error: {e}")
            st.session_state.faiss_ready = False
            
    except Exception as e:
        print(f"Error loading existing data: {e}")
        st.session_state.docs_index = []
        st.session_state.chunks = []
        st.session_state.all_docs = []
        st.session_state.faiss_ready = False

# --- Main App ---
def show_main_app():
    with st.sidebar:
        if st.session_state.username:
            st.markdown("### 👤 User Profile")
            st.markdown(f"**Logged in as:** {st.session_state.username}")
            st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            if st.session_state.session_token:
                logout_session(st.session_state.session_token)
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.session_token = None
            st.rerun()
    
    st.markdown("<h1 style='text-align: center; color: #1976d2;'>🧠 RAG Intelligence System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64b5f6; font-size: 18px;'>Upload documents and get intelligent answers</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "💬 Ask Questions", "📚 Document Library"])
    
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📤 Upload Documents")
    
        uploaded_files = st.file_uploader(
            "Supported formats: PDF, DOCX, TXT, MD, CSV, XLSX",
            type=["pdf", "docx", "txt", "md", "csv", "xlsx"],
            accept_multiple_files=True,
            key="file_uploader"
        )
    
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} file(s) selected")
        
            if st.button("🚀 Process Documents", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
            
                all_docs = []
                all_chunks = []
                
                if os.path.exists(DOCS_INDEX_PATH):
                    with open(DOCS_INDEX_PATH, "r") as f:
                        all_docs = json.load(f)
            
                if os.path.exists(RAG_CHUNKS_PATH):
                    with open(RAG_CHUNKS_PATH, "r") as f:
                        all_chunks = json.load(f)
            
                new_chunks = []
            
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Processing {file.name}...")
                
                    try:
                        file_bytes = file.read()
                        doc_meta, chunks = ingest_file(file_bytes, file.name, username=st.session_state.username)
                    
                        all_docs.append(doc_meta)
                        new_chunks.extend(chunks)
                        
                        log_document_to_db(doc_meta, len(chunks), username=st.session_state.username)
                    
                        st.success(f"✅ {file.name}: {len(chunks)} chunks created")
                    
                    except Exception as e:
                        st.error(f"❌ Error processing {file.name}: {str(e)}")
                        print(f"Error processing {file.name}: {e}")
                        traceback.print_exc()
                
                    progress_bar.progress((idx + 1) / len(uploaded_files))
            
                all_chunks.extend(new_chunks)
                save_index_and_chunks(all_docs, all_chunks)
            
                status_text.text("Updating FAISS index...")
                try:
                    build_faiss_index(new_chunks, append=True)
                    st.session_state.faiss_ready = True
                    
                    load_existing_data()
                    
                    status_text.text("✅ All documents processed!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error building FAISS index: {e}")
                    print(f"FAISS error: {e}")
                    traceback.print_exc()
    
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        if not st.session_state.faiss_ready:
            st.warning("⚠️ Please upload and process documents first!")
        else:
            st.subheader("💬 Ask a Question")
            
            question = st.text_input(
                "Enter your question:",
                placeholder="What would you like to know?",
                key="question_input"
            )
            
            search_button = st.button("🔍 Get Answer", type="primary", use_container_width=True)
            
            top_k = 3
            threshold = 0.7
            
            if search_button and question:
                with st.spinner("🤔 Thinking..."):
                    try:
                        current_username = st.session_state.get('username', 'anonymous')
                        
                        result = rag_pipeline(
                            question,
                            st.session_state.chunks,
                            top_k=top_k,
                            threshold=threshold,
                            username=current_username,
                            user_doc_ids=None
                        )     

                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": result["answer"],
                            "sources": result["sources"]
                        })
                        
                        st.info(f"⏱️ Response Time: {result.get('latency_ms', 0):.2f}ms")
                        
                        st.markdown("### 🎯 Answer")
                        st.markdown(f"<div class='answer-box'>{result['answer']}</div>", unsafe_allow_html=True)
                        
                        if result["sources"]:
                            st.markdown("### 📚 Top Source")
                            source = result["sources"][0]
                            with st.expander(f"📄 {source['filename']} (Page {source['page']}) - Relevance: {source['score']:.3f}", expanded=True):
                                st.markdown(f"**Document Type:** {source['type']}")
                                st.markdown(f"**Content Preview:**")
                                st.text(source['content'][:400] + "..." if len(source['content']) > 400 else source['content'])
                    except Exception as e:
                        st.error(f"Error processing query: {e}")
                        print(f"Query error: {e}")
                        traceback.print_exc()
            
            if st.session_state.chat_history:
                st.markdown("---")
                st.markdown("### 📜 Recent Questions")
                for i, chat in enumerate(reversed(st.session_state.chat_history[-5:]), 1):
                    with st.expander(f"Q{i}: {chat['question'][:50]}..."):
                        st.markdown(f"**Answer:** {chat['answer']}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📚 Document Library")
        
        if not st.session_state.docs_index:
            st.info("No documents uploaded yet.")
        else:
            for doc in st.session_state.docs_index:
                with st.expander(f"📄 {doc['filename']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Pages", doc['text_files_count'])
                    with col2:
                        st.metric("Tables", doc['tables_count'])
                    with col3:
                        st.metric("Images", doc['images_count'])
                    
                    st.markdown(f"**Document ID:** `{doc['doc_id']}`")
                    st.markdown(f"**Type:** {doc['ext']}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- Main Execution ---
def main():
    try:
        init_session_state()
        load_css()
        
        if st.session_state.logged_in and (not st.session_state.docs_index or not st.session_state.chunks):
            load_existing_data()
        
        if not st.session_state.logged_in:
            show_auth_page()
        else:
            show_main_app()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.error("Please refresh the page or check the console for details.")
        print(f"Main app error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()