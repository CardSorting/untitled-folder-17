import firebase_admin
from firebase_admin import credentials, auth
import json
import os

def init_firebase(app):
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            # Try to get credentials from environment
            cred_json = app.config.get('FIREBASE_CREDENTIALS')
            if not cred_json:
                # Fallback to file if environment variable not set
                cred_path = app.config.get('FIREBASE_CREDENTIALS_PATH')
                if not cred_path:
                    raise ValueError("Neither FIREBASE_CREDENTIALS nor FIREBASE_CREDENTIALS_PATH set in config")
                
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at {cred_path}")
                
                try:
                    with open(cred_path, 'r') as f:
                        cred_json = json.load(f)
                        print(f"Successfully loaded credentials from {cred_path}")
                except json.JSONDecodeError as e:
                    print(f"Error parsing credentials JSON: {e}")
                    raise
                except Exception as e:
                    print(f"Error reading credentials file: {e}")
                    raise
            
            try:
                cred = credentials.Certificate(cred_json)
                print("Successfully created Firebase credentials certificate")
            except Exception as e:
                print(f"Error creating Firebase credentials certificate: {e}")
                raise
            
            try:
                firebase_admin.initialize_app(cred)
                print("Successfully initialized Firebase Admin SDK")
            except Exception as e:
                print(f"Error initializing Firebase Admin SDK: {e}")
                raise
            
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}")
            # Continue without Firebase Admin SDK
            pass

def verify_firebase_token(id_token):
    """Verify Firebase ID token"""
    try:
        if not firebase_admin._apps:
            raise ValueError("Firebase Admin SDK not initialized")
        
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Unexpected error verifying token: {e}")
        return None
