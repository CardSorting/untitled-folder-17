import firebase_admin
from firebase_admin import credentials, auth
import json

def init_firebase(app):
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            # Try to get credentials from environment variable first
            if app.config.get('FIREBASE_CREDENTIALS'):
                cred_dict = app.config['FIREBASE_CREDENTIALS']
                if isinstance(cred_dict, str):
                    cred_dict = json.loads(cred_dict)
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback to file
                cred_path = app.config.get('FIREBASE_CREDENTIALS_PATH')
                if not cred_path:
                    raise ValueError("No Firebase credentials found in environment or file system")
                cred = credentials.Certificate(cred_path)
            
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Warning: Failed to initialize Firebase Admin SDK: {e}")
            # Continue without Firebase Admin SDK
            pass

def verify_firebase_token(id_token):
    """Verify Firebase ID token"""
    try:
        if not firebase_admin._apps:
            print("Warning: Firebase Admin SDK not initialized")
            return None
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None
