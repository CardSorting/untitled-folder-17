from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from ..models.user import User
from ..utils.firebase import verify_firebase_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user with Firebase token and create/retrieve user record."""
    try:
        # Check if user is already authenticated
        if current_user.is_authenticated:
            return jsonify({
                'message': 'Already authenticated',
                'user': current_user.to_dict()
            }), 200

        # Get and verify token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'No token provided'}), 401

        decoded_token = verify_firebase_token(token)
        if not decoded_token:
            return jsonify({'message': 'Invalid or expired token'}), 401
            
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        
        if not firebase_uid or not email:
            return jsonify({'message': 'Incomplete user information in token'}), 400
        
        # Get or create user
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            try:
                user = User.create_user(firebase_uid=firebase_uid, email=email)
            except Exception as e:
                return jsonify({
                    'message': 'Failed to create user',
                    'error': str(e)
                }), 500
        
        # Log in the user
        login_user(user, remember=True)
            
        return jsonify({
            'message': 'Authentication successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'message': 'Authentication failed',
            'error': str(e)
        }), 500

@auth_bp.route('/validate', methods=['POST'])
def validate_token():
    """Validate the current session token."""
    try:
        # Get and verify token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'valid': False, 'message': 'No token provided'}), 401

        decoded_token = verify_firebase_token(token)
        if not decoded_token:
            return jsonify({'valid': False, 'message': 'Invalid or expired token'}), 401
            
        firebase_uid = decoded_token.get('uid')
        if not firebase_uid:
            return jsonify({'valid': False, 'message': 'Invalid user information in token'}), 401
        
        # Check if user exists
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'valid': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'message': 'Token is valid',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': 'Token validation failed',
            'error': str(e)
        }), 500

@auth_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """Update session activity timestamp."""
    try:
        # Get and verify token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'valid': False, 'message': 'No token provided'}), 401

        decoded_token = verify_firebase_token(token)
        if not decoded_token:
            return jsonify({'valid': False, 'message': 'Invalid or expired token'}), 401
            
        firebase_uid = decoded_token.get('uid')
        if not firebase_uid:
            return jsonify({'valid': False, 'message': 'Invalid user information in token'}), 401
        
        # Check if user exists
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'valid': False, 'message': 'User not found'}), 404
        
        # Update last activity timestamp if needed
        user.update_last_activity()
        
        return jsonify({
            'valid': True,
            'message': 'Heartbeat received'
        }), 200
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': 'Heartbeat failed',
            'error': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    if current_user.is_authenticated:
        logout_user()
        return jsonify({'message': 'Successfully logged out'}), 200
    return jsonify({'message': 'No user to log out'}), 400

@auth_bp.route('/user', methods=['GET'])
def get_current_user():
    """Get the current user's information."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    return jsonify({
        'authenticated': False,
        'user': None
    }), 200
