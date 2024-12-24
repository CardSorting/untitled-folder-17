import firebase_admin
from firebase_admin import credentials, auth
import json

def init_firebase(app):
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Try to get credentials from environment variable first
        if app.config.get('FIREBASE_CREDENTIALS'):
            cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
        else:
            # Fallback to file
            cred_path = app.config.get('FIREBASE_CREDENTIALS_PATH')
            if cred_path:
                cred = credentials.Certificate(cred_path)
            else:
                raise ValueError("No Firebase credentials found in environment or file system")
        
        firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token):
    """Verify Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None
