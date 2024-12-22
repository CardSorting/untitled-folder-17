import firebase_admin
from firebase_admin import credentials

def initialize_firebase(app_config):
    """Initialize Firebase Admin SDK with credentials from config."""
    cred_path = app_config['FIREBASE_CREDENTIALS_PATH']
    cred_object = credentials.Certificate(cred_path)
    
    try:
        firebase_admin.initialize_app(cred_object)
    except ValueError:
        # App already initialized
        pass

def verify_firebase_token(token):
    """Verify Firebase ID token and return decoded token."""
    from firebase_admin import auth
    from flask import current_app
    import json
    
    if not token:
        current_app.logger.error("No token provided")
        return None
        
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split('Bearer ')[1]
        
        # Log token details (without sensitive parts)
        token_parts = token.split('.')
        if len(token_parts) == 3:
            import base64
            try:
                # Add padding if needed
                header_part = token_parts[0]
                padding = 4 - (len(header_part) % 4)
                if padding != 4:
                    header_part += '=' * padding
                
                # Decode header
                header_bytes = base64.b64decode(header_part)
                header = json.loads(header_bytes)
                current_app.logger.info(f"Token header: {header}")
            except Exception as e:
                current_app.logger.warning(f"Could not decode token header: {str(e)}")
            
        decoded_token = auth.verify_id_token(token)
        current_app.logger.info(f"Successfully verified token for user: {decoded_token.get('email')}")
        return decoded_token
        
    except auth.InvalidIdTokenError:
        current_app.logger.error("Invalid token")
        return None
    except auth.ExpiredIdTokenError:
        current_app.logger.error("Expired token")
        return None
    except auth.RevokedIdTokenError:
        current_app.logger.error("Revoked token")
        return None
    except auth.CertificateFetchError:
        current_app.logger.error("Error fetching certificates")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error verifying token: {str(e)}")
        return None
