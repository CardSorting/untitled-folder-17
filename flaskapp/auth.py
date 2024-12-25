from flask import Blueprint, request, jsonify, current_app
from .firebase import verify_firebase_token
from functools import wraps
import firebase_admin
from firebase_admin import auth as firebase_auth

bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        try:
            # Verify the Firebase token
            decoded_token = verify_firebase_token(auth_header)
            if not decoded_token:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Add the user info to the request context
            request.user = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name')
            }
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Auth error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function

@bp.route('/login', methods=['POST'])
def login():
    try:
        # Get the ID token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        # Verify the Firebase token
        decoded_token = verify_firebase_token(auth_header)
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401

        # Get additional user info from Firebase
        try:
            user = firebase_auth.get_user(decoded_token['uid'])
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'name': user.display_name,
                'photo_url': user.photo_url
            }
        except Exception as e:
            current_app.logger.error(f"Error getting user info: {e}")
            user_data = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name')
            }

        return jsonify({
            'message': 'Successfully logged in',
            'user': user_data
        })

    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 401

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    return jsonify({'message': 'Successfully logged out'})
