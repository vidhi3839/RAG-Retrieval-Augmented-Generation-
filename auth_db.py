# auth_db.py
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import hashlib
import uuid
from datetime import datetime, timedelta

def get_supabase_client():
    """Get Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, display_name=None):
    """Create a new user in the database with optional display name."""
    try:
        supabase: Client = get_supabase_client()
        password_hash = hash_password(password)
        
        if not display_name:
            display_name = username.split("@")[0] if "@" in username else username
        
        payload = {
            "username": username,
            "email": username,  
            "password_hash": password_hash,
            "display_name": display_name
        }
        
        result = supabase.table("users").insert(payload).execute()
        return {"success": True, "user": result.data[0]}
    except Exception as e:
        error_msg = str(e)
        if "duplicate key" in error_msg.lower() or "unique" in error_msg.lower():
            return {"success": False, "error": "Username already exists"}
        return {"success": False, "error": str(e)}
    
def verify_user(username, password):
    """Verify user credentials."""
    try:
        supabase: Client = get_supabase_client()
        password_hash = hash_password(password)
        
        result = supabase.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            return {"success": False, "error": "User not found"}
        
        user = result.data[0]
        
        if user["password_hash"] != password_hash:
            return {"success": False, "error": "Incorrect password"}
        
        # Update last login
        supabase.table("users").update({
            "last_login": datetime.now().isoformat()
        }).eq("id", user["id"]).execute()
        
        return {"success": True, "user": user}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_session(user_id, display_name):
    """Create a new session for the user."""
    try:
        supabase: Client = get_supabase_client()
        
        session_token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7) 
        
        payload = {
            "user_id": user_id,
            "username": display_name, 
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "is_active": True
        }
        
        result = supabase.table("sessions").insert(payload).execute()
        return {"success": True, "session": result.data[0], "token": session_token}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def validate_session(session_token):
    """Validate if a session is still active and not expired."""
    try:
        supabase: Client = get_supabase_client()
        
        result = supabase.table("sessions").select("*").eq("session_token", session_token).eq("is_active", True).execute()
        
        if not result.data:
            return {"valid": False, "error": "Session not found"}
        
        session = result.data[0]
        expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
        
        if datetime.now(expires_at.tzinfo) > expires_at:
            # Session expired, deactivate it
            supabase.table("sessions").update({"is_active": False}).eq("id", session["id"]).execute()
            return {"valid": False, "error": "Session expired"}
        
        return {"valid": True, "session": session}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def logout_session(session_token):
    """Deactivate a session (logout)."""
    try:
        supabase: Client = get_supabase_client()
        
        supabase.table("sessions").update({
            "is_active": False
        }).eq("session_token", session_token).execute()
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_sessions(user_id, active_only=True):
    """Get all sessions for a user."""
    try:
        supabase: Client = get_supabase_client()
        
        query = supabase.table("sessions").select("*").eq("user_id", user_id)
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.execute()
        return {"success": True, "sessions": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}
