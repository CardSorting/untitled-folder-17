import os
import base64
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user, login_required
import google.generativeai as genai
from datetime import datetime
from ..utils.backblaze import b2_client

companion_bp = Blueprint('companion', __name__, url_prefix='/companion')

# Configure Google Generative AI
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

@companion_bp.route('/')
@login_required
def companion():
    """Render the AI companion page."""
    return render_template('companion/index.html')

@companion_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages and return AI response."""
    try:
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
            
        data = request.json
        user_message = data.get('message')
        request_id = data.get('request_id')
        
        if not user_message:
            return jsonify({'error': 'No message provided', 'request_id': request_id}), 400
        
        if not request_id:
            return jsonify({'error': 'No request ID provided'}), 400

        # Get AI response using Gemini
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found in environment variables")
        
        # Generate response with system prompt and user message
        chat = model.start_chat(history=[])
        response = chat.send_message(
            f"""You are a helpful and friendly AI companion. Keep responses concise and engaging.
            User message: {user_message}"""
        )
        
        ai_message = response.text
        
        # Save message to Firestore
        current_user.save_message(user_message, ai_message, request_id)
        
        return jsonify({
            'message': ai_message,
            'request_id': request_id
        })

    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'request_id': request_id if 'request_id' in locals() else None
        }), 500

@companion_bp.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    """Get user's chat history."""
    try:
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
            
        limit = request.args.get('limit', default=50, type=int)
        messages = current_user.get_chat_history(limit=limit)
        
        return jsonify({
            'messages': messages
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@companion_bp.route('/upload-audio', methods=['POST'])
@login_required
def upload_audio():
    """Handle audio upload to Backblaze B2."""
    try:
        data = request.json
        audio_data = data.get('audio')
        
        if not audio_data:
            return jsonify({'error': 'No audio data provided'}), 400
            
        # Decode base64 audio data
        try:
            # Remove data URL prefix if present
            if 'base64,' in audio_data:
                audio_data = audio_data.split('base64,')[1]
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            return jsonify({'error': 'Invalid audio data format'}), 400

        # Upload to Backblaze B2
        result = b2_client.upload_audio(audio_bytes, current_user.firebase_uid)
        
        if not result['success']:
            raise Exception(result.get('error', 'Upload failed'))

        # Save audio URL to user's chat history in Firestore
        current_user.save_message(
            user_message="[Audio Message]",
            ai_response="",
            request_id=data.get('request_id', ''),
            audio_url=result['url']
        )
            
        return jsonify({
            'message': 'Audio uploaded successfully',
            'url': result['url']
        })

    except Exception as e:
        current_app.logger.error(f"Error uploading audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@companion_bp.route('/recordings', methods=['GET'])
@login_required
def get_recordings():
    """Get user's audio recordings."""
    try:
        result = b2_client.list_user_recordings(current_user.firebase_uid)
        
        if not result['success']:
            raise Exception(result.get('error', 'Failed to list recordings'))
            
        return jsonify({
            'recordings': result['files']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting recordings: {str(e)}")
        return jsonify({'error': str(e)}), 500
