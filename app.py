import streamlit as st
import json
import os
from pathlib import Path
import traceback
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Import your modules with error handling
try:
    from ingestion import ingest_file, save_index_and_chunks
    from retrieval import build_faiss_index, load_faiss_index
    from generation import rag_pipeline
    from database import log_document_to_db, log_chunks_to_db
    from config import *
    from auth_db import create_user, verify_user, create_session, validate_session, logout_session
    from admin_analytics import show_admin_dashboard
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
    if "email" not in st.session_state:
        st.session_state.email = None
    if "display_name" not in st.session_state:
        st.session_state.display_name = None
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
    if "current_page" not in st.session_state:
        st.session_state.current_page = "main"
    
    # Validate existing session on page load
    if st.session_state.session_token:
        try:
            validation = validate_session(st.session_state.session_token)
            if not validation["valid"]:
                st.session_state.logged_in = False
                st.session_state.email = None
                st.session_state.display_name = None
                st.session_state.session_token = None
            else:
                session_data = validation.get("session", {})
                if session_data.get("display_name"):
                    st.session_state.display_name = session_data["display_name"]
        except Exception as e:
            print(f"Session validation error: {e}")
            st.session_state.logged_in = False
            st.session_state.email = None
            st.session_state.display_name = None
            st.session_state.session_token = None

# --- Custom CSS ---
def load_css():
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 0rem !important;}
    
    .stApp {
        background: linear-gradient(135deg, #133E87 0%, #608BC1 50%, #133E87 100%);
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
    
    .st-emotion-cache-kgpedg{
                margin: -30px !important;
    }
                
    div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-baseweb="input"] > div {
        background-color: white !important;
        border: none !important;
        box-shadow: none !important;
        padding: 4px 10px !important;
        height: 38px !important;
        border-radius: 6px !important;
    }

    div[data-baseweb="input"] input {
        background-color: white !important;
        border: none !important;
        box-shadow: none !important;
        color: #091057 !important;
        padding: 0 !important;
        margin: 0 !important;
        height: 26px !important;       
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"]:focus-within > div {
        border: none !important;
        box-shadow: none !important;
    }

    input:-webkit-autofill,
    input:-webkit-autofill:focus {
        -webkit-box-shadow: 0 0 0 1000px white inset !important;
        box-shadow: none !important;
    }

    input[type="password"]:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    input::placeholder {
        color: #091057 !important;
        opacity: 1 !important;
    }

    .stButton button {
        background: transparent !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        width: 100% !important;
        height: 36px !important;
        margin-right: 0px;
        margin-left: 40%;
        transition: all 0.3s ease !important;
    }
            
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px transparent !important;
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
    
    .st-emotion-cache-qcpnpn {
        border: none !important;
    }

    .st-emotion-cache-qcpnpn button{
        width: 100px !important;
    }

        .st-emotion-cache-qcpnpn button:hover{
        width: 100px !important;
        color: #e3f2fd !important;
        border-color: #e3f2fd !important;
    }  
                        .st-emotion-cache-qcpnpn button::after{
        width: 100px !important;
        color: #e3f2fd !important;
        border-color: #e3f2fd !important;
    }         
    .st-emotion-cache-qcpnpn label{
            color: #F3F3E0 !important;
                }
                
       .st-emotion-cache-qcpnpn imput{
            color: #091057 !important;
                }  

    .st-eb:hover{
                color: black !important;
                }       

    .st-ef {
    background-color: black !important;
}
                .st-emotion-cache-14553y9{
                color: white !important;
                }
.st-emotion-cache-14553y9 p:hover{
                color: black !important;
                }
        .st-emotion-cache-kgpedg {
                padding-top:30px !important;
            }        
 /* Action buttons (Get Answer, Process Documents) - Gradient style */
    button[kind="primary"] {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important;
        color: #1565c0 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        width: auto !important;
        height: auto !important;
        margin-left: 85% !important;
        box-shadow: 0 4px 12px rgba(66, 165, 245, 0.2) !important;
        transition: all 0.3s ease !important;
        border-left: 4px solid #42a5f5 !important;
    }
            
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(66, 165, 245, 0.3) !important;
    }

                
/* File Uploader - Styled like Answer Box */
[data-testid="stFileUploader"] {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important;
    padding: 25px !important;
    border-radius: 15px !important;
    border-left: 5px solid #42a5f5 !important;
    margin: 15px 0 !important;
}

/* File uploader section */
[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: 2px dashed #42a5f5 !important;
    border-radius: 10px !important;
    padding: 20px !important;
}

/* Drag and drop text */
[data-testid="stFileUploader"] section small {
    color: #133E87 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Browse files button */
[data-testid="stFileUploader"] section button {
    background: #133E87 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    margin-left: 0px !important;
    width: auto !important;
}

[data-testid="stFileUploader"] section button:hover {
    background: #1976d2 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(66, 165, 245, 0.3) !important;
}

/* File limit text */
[data-testid="stFileUploader"] small {
    color: #133E87 !important;
    font-weight: 500 !important;
}

/* Uploaded file names */
[data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
    color: #1565c0 !important;
    font-weight: 600 !important;
}

/* Delete button for uploaded files */
[data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] {
    color: #c62828 !important;
}
    .stFileUploader label,
    .stFileUploader small,
    .stFileUploader span,
    .stFileUploader div {
        color: #133E87 !important;
    }

    .st-emotion-cache-s1invk:hover{
                color: black !important;
            
                }            
    .st-d1{
                background-color: white !important;
        color: #133E87 !important;
        }
      
                                </style>
    """, unsafe_allow_html=True)

# --- Login/Signup Page ---
def show_auth_page():
    """Login + Signup with Email and Display Name."""
    import traceback
    
    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False

    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([1, 1], gap="medium")

    with left_col:
        st.markdown('<div style="padding: 30px 24px; border-radius: 14px;">', unsafe_allow_html=True)

        # ============ SIGNUP VIEW ============
        if st.session_state.show_signup:
            st.markdown(
                '<h1 style="color: #F3F3E0; text-align: center; margin-bottom: 6px; font-size: 36px;">Create Account</h1>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p style="text-align:center; color:#F3F3E0; margin-bottom:20px; font-weight: bold;">Join the RAG Intelligence System</p>',
                unsafe_allow_html=True,
            )

            with st.form("signup_form"):
                new_name = st.text_input("Full Name", key="signup_name", placeholder="Enter your full name")
                new_email = st.text_input("Email", key="signup_email", placeholder="example@email.com")
                new_password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Confirm password")

                row = st.columns([1, 3, 1])

                with row[0]:
                    submitted = st.form_submit_button("Create")

                with row[2]:
                    back_clicked = st.form_submit_button("Login")

                if submitted:
                    if not new_name.strip() or not new_email.strip() or not new_password:
                        st.warning("⚠️ Please fill all fields")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(new_password) < 6:
                        st.warning("⚠️ Password must be at least 6 characters")
                    elif "@" not in new_email or "." not in new_email:
                        st.warning("⚠️ Please enter a valid email address")
                    else:
                        try:
                            res = create_user(new_email.strip(), new_password, new_name.strip())
                            if res.get("success"):
                                st.success("✅ Account created! Please login.")
                                st.session_state.show_signup = False
                                st.rerun()
                            else:
                                st.error("❌ " + res.get("error", "Failed to create account"))
                        except Exception as e:
                            st.error("❌ Sign-up error.")
                            print("Sign-up error:", e)
                            traceback.print_exc()

                if back_clicked:
                    st.session_state.show_signup = False
                    st.rerun()

        # ============ LOGIN VIEW ============
        else:
            st.markdown(
                '<h1 style="color: #F3F3E0; text-align: center; margin-bottom: 6px; font-size: 40px;">Login</h1>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p style="text-align:center; color:#F3F3E0; margin-bottom:20px;">RAG Intelligence System</p>',
                unsafe_allow_html=True,
            )

            col_label1, col_input1 = st.columns([1, 3])
            with col_label1:
                st.markdown("<div style='padding-top:8px;'><label style='font-size:24px; color:#F3F3E0; font-weight:500;'>Email</label></div>", unsafe_allow_html=True)
            with col_input1:
                login_email = st.text_input("Email", key="login_email", placeholder="example@email.com", label_visibility="collapsed")

            st.markdown("<div style='margin:8px 0;'></div>", unsafe_allow_html=True)

            col_label2, col_input2 = st.columns([1, 3])
            with col_label2:
                st.markdown("<div style='padding-top:8px;'><label style='font-size:24px; color:#F3F3E0; font-weight:500;'>Password</label></div>", unsafe_allow_html=True)
            with col_input2:
                login_pass = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password", label_visibility="collapsed")

            st.markdown("<div style='margin:12px 0;'></div>", unsafe_allow_html=True)

            with st.form("login_form"):
                row = st.columns([1, 3, 1])

                with row[0]:
                    submit = st.form_submit_button("Login")

                with row[2]:
                    signup_clicked = st.form_submit_button("Sign up")

                if submit:
                    if not (login_email or "").strip() or not (login_pass or ""):
                        st.warning("⚠️ Please fill all fields")
                    else:
                        try:
                            result = verify_user(login_email.strip(), login_pass)
                            if result.get("success"):
                                user = result.get("user")
                                display_name = user.get("display_name", user.get("username", login_email.split("@")[0]))
                                
                                session_res = create_session(
                                    user["id"], 
                                    display_name
                                )
                                
                                if session_res.get("success"):
                                    st.session_state.logged_in = True
                                    st.session_state.email = login_email.strip()
                                    st.session_state.display_name = display_name
                                    st.session_state.session_token = session_res.get("token")
                                    st.success(f"✅ Welcome, {display_name}!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to create session")
                            else:
                                st.error("❌ " + result.get("error", "Invalid credentials"))
                        except Exception as e:
                            st.error("❌ Login error.")
                            print("Login error:", e)
                            traceback.print_exc()

                if signup_clicked:
                    st.session_state.show_signup = True
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Right column - How RAG Works
    with right_col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #F3F3E0; text-align: center; margin-bottom: 20px; font-size: 28px;'>⚡ How RAG Works</h2>", unsafe_allow_html=True)

        st.markdown("""
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;'>
            <div style='background: white; padding: 12px; border-radius: 12px; box-shadow: 0 6px 14px rgba(100, 181, 246, 0.16); border-top: 3px solid #64b5f6; text-align: center;'>
                <div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin: 0 auto 8px;'>📄</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 14px; margin-bottom: 4px;'>1. Upload</div>
                <div style='color: #64b5f6; font-size: 13px;'>Documents</div>
            </div>
            <div style='background: white; padding: 12px; border-radius: 12px; box-shadow: 0 6px 14px rgba(66, 165, 245, 0.16); border-top: 3px solid #42a5f5; text-align: center;'>
                <div style='background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%); width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: white; margin: 0 auto 8px;'>⚡</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 14px; margin-bottom: 4px;'>2. Embeddings</div>
                <div style='color: #64b5f6; font-size: 13px;'>Vectorize</div>
            </div>
        </div>

        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px;'>
            <div style='background: white; padding: 12px; border-radius: 12px; box-shadow: 0 6px 14px rgba(66, 165, 245, 0.16); border-top: 3px solid #1e88e5; text-align: center;'>
                <div style='background: linear-gradient(135deg, #90caf9 0%, #42a5f5 100%); width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin: 0 auto 8px;'>🔍</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 14px; margin-bottom: 4px;'>3. Search</div>
                <div style='color: #64b5f6; font-size: 13px;'>FAISS Index</div>
            </div>
            <div style='background: white; padding: 12px; border-radius: 12px; box-shadow: 0 6px 14px rgba(25, 118, 210, 0.12); border-top: 3px solid #1976d2; text-align: center;'>
                <div style='background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%); width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: white; margin: 0 auto 8px;'>🤖</div>
                <div style='color: #1976d2; font-weight: 600; font-size: 14px; margin-bottom: 4px;'>4. Generate</div>
                <div style='color: #64b5f6; font-size: 13px;'>AI Answer</div>
            </div>
        </div>

        <div style='text-align:center; margin-top: 18px; padding-top: 14px; border-top: 1px solid rgba(100, 181, 246, 0.12);'>
            <div style='color: #F3F3E0; font-weight: 600; font-size: 18px;'>Retrieval-Augmented Generation</div>
            <div style='color: #F3F3E0; font-size: 15px;'>Smart answers from your documents</div>
        </div>
        """, unsafe_allow_html=True)


# --- Load Existing Data ---
def load_existing_data():
    """Load all documents and chunks."""
    try:
        if os.path.exists(DOCS_INDEX_PATH):
            with open(DOCS_INDEX_PATH, "r") as f:
                all_docs = json.load(f)
                st.session_state.all_docs = all_docs
                
                user_identifier = st.session_state.display_name 
                if user_identifier:
                    st.session_state.docs_index = [
                        doc for doc in all_docs 
                        if doc.get('uploaded_by') == user_identifier
                    ]
        
        if os.path.exists(RAG_CHUNKS_PATH):
            with open(RAG_CHUNKS_PATH, "r") as f:
                st.session_state.chunks = json.load(f)
            print(f"🔍 {len(st.session_state.chunks)} total chunks available for querying")
        
        try:
            index, mapping = load_faiss_index()
            if index is not None:
                st.session_state.faiss_ready = True
        except Exception as e:
            st.session_state.faiss_ready = False
            
    except Exception as e:
        print(f"Error loading data: {e}")
        st.session_state.docs_index = []
        st.session_state.chunks = []

def get_user_query_history(username, limit=None):
    """Get all past queries for a user from database."""
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        query = supabase.table("queries").select(
            "question, answer, sources, created_at, avg_similarity_score"
        ).eq("username", username).order("created_at", desc=True)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching query history: {e}")
        return []
# --- Main App ---

def show_main_app():
    st.markdown("""
    <style>
    
          
    /* Sidebar navigation buttons - LEFT ALIGNED */
    [data-testid="stSidebar"] .stButton button {
        text-align: center !important;
        justify-content: flex-start !important;
        padding-left: 1rem !important;
        width: 100% !important;
        margin-left: 0px !important;
        background-color: transparent !important;
        color: #fff !important;
    }
    
    /* Override center alignment for sidebar buttons */
    [data-testid="stSidebar"] .stButton {
        text-align: left !important;
    }
    

    </style>
                
    

    """, unsafe_allow_html=True)
    
    is_admin = st.session_state.email == "admin@gmail.com"

    with st.sidebar:
        if st.session_state.display_name:
            st.markdown("### 👤 User Profile")
            st.markdown(f"**{st.session_state.display_name}**")
            st.markdown("---")
            
            if is_admin:
                st.markdown("🔑 **Admin Account**")
                st.markdown("---")

            if is_admin:
                st.markdown("### 🧭 Navigation")
                if st.button("Main Dashboard", use_container_width=True):
                    st.session_state.current_page = "main"
                    st.rerun()
    
                if st.button("Admin Analytics", use_container_width=True):
                    st.session_state.current_page = "analytics"
                    st.markdown("---")
                    st.rerun()
            
            
            st.markdown("### 📚 Your Documents")

            if st.session_state.docs_index:
                user_docs = [
                    d for d in st.session_state.docs_index
                    if d.get("uploaded_by") == st.session_state.display_name
                ]
                print("Docs",user_docs)
                if user_docs:
                    for doc in user_docs:
                        st.markdown(f"- **{doc['filename']}**")
                else:
                    st.info("No documents uploaded yet.")
            else:
                st.info("No documents uploaded yet.")

            st.markdown("---")
    
        st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.button("Logout"):
            if st.session_state.session_token:
                logout_session(st.session_state.session_token)
            st.session_state.logged_in = False
            st.session_state.email = None
            st.session_state.display_name = None
            st.session_state.session_token = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if is_admin and st.session_state.current_page == "analytics":
        show_admin_dashboard()
        return
    
    # MAIN DASHBOARD
    st.markdown("<h1 style='text-align: center; color: #F3F3E0;'>RAG Intelligence System</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #F3F3E0; font-size: 24px;'>Welcome, {st.session_state.display_name}! 👋</p>", unsafe_allow_html=True)

    st.markdown("## Ask a Question")

    if not st.session_state.faiss_ready:
        st.warning("⚠️ Upload and process documents before asking questions.")
    else:
        question = st.text_input("Ask your question:", placeholder="Type your question here...", key="question_input")
        st.markdown('<div class="get-answer-btn">', unsafe_allow_html=True)
        ask = st.button(" Get Answer", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if ask and question:
            with st.spinner(" Thinking..."):
                try:
                    result = rag_pipeline(
                        question,
                        st.session_state.chunks,
                        top_k=3,
                        threshold=0.7,
                        username=st.session_state.display_name,
                        user_doc_ids=None
                    )

                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": result["answer"],
                        "sources": result["sources"]
                    })

                    st.info(f"⏱️ Response Time: {result.get('latency_ms', 0):.2f}ms")
                    st.markdown("###  Answer")
                    st.markdown(f"<div class='answer-box'>{result['answer']}</div>", unsafe_allow_html=True)

                    # if result["sources"]:
                    #     st.markdown("###  Source Used")
                    #     src = result["sources"][0]
                    #     with st.expander(f" {src['filename']} (Page {src['page']})", expanded=True):
                    #         st.text(src['content'])

                except Exception as e:
                    st.error(f"Error: {e}")
                    traceback.print_exc()

    st.markdown("##  Upload Documents")
    uploaded_files = st.file_uploader(
        "Supported formats: PDF, DOCX, TXT, MD, CSV, XLSX",
        type=["pdf", "docx", "txt", "md", "csv", "xlsx"],
        accept_multiple_files=True,
        key="file_uploader"
    )

    if uploaded_files:
        st.info(f" {len(uploaded_files)} file(s) selected")

        if st.button(" Process Documents", type="primary"):
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
                    doc_meta, chunks = ingest_file(file_bytes, file.name, username=st.session_state.display_name)

                    all_docs.append(doc_meta)
                    new_chunks.extend(chunks)

                    log_document_to_db(doc_meta, len(chunks), username=st.session_state.display_name)
                    log_chunks_to_db(chunks) 
                    
                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {str(e)}")
                    traceback.print_exc()

                progress_bar.progress((idx + 1) / len(uploaded_files))

            all_chunks.extend(new_chunks)
            save_index_and_chunks(all_docs, all_chunks)

            status_text.text("Processing...")
            try:
                build_faiss_index(new_chunks, append=True)
                st.session_state.faiss_ready = True
                load_existing_data()

                status_text.text(" All documents processed!")

            except Exception as e:
                st.error(f"Error building FAISS index: {e}")
                traceback.print_exc()

    st.markdown("---")

    st.markdown("##  All Your Questions")

# Fetch all queries from database
    user_queries = get_user_query_history(st.session_state.display_name)

    if user_queries:
        st.info(f" Total Questions: {len(user_queries)}")
    
        for i, query in enumerate(user_queries, 1):
        # Parse sources from JSON string
            try:
                sources = json.loads(query.get('sources', '[]')) if isinstance(query.get('sources'), str) else query.get('sources', [])
            except:
                sources = []
        
        # Format timestamp
            created_at = query.get('created_at', '')
            if created_at:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%b %d, %Y at %I:%M %p')
            else:
                time_str = ''
        
        # Show question with metadata
            similarity = query.get('avg_similarity_score', 0)
            with st.expander(
                f"Q: {query['question'][:70]}... | {time_str}",
                expanded=(i == 1)  # First question expanded by default
            ):
                st.markdown(f"**Question:** {query['question']}")
                st.markdown(f"**Answer:** {query['answer']}")
            
                # if sources:
                #     st.markdown(f"**Sources:**")
                #     for src in sources[:1]: 
                #         st.caption(f" {src.get('filename', 'Unknown')} (Page {src.get('page', 'N/A')}) ")
    else:
        st.info("No questions asked yet. Start by uploading documents and asking questions!")


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
        print(f"Main app error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
