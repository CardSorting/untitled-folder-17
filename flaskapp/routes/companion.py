import os
from flask import Blueprint, render_template, request, jsonify, current_app
import google.generativeai as genai
from datetime import datetime

companion_bp = Blueprint('companion', __name__, url_prefix='/companion')

# Configure Google Generative AI
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

@companion_bp.route('/')
def companion():
    """Render the AI companion page."""
    return render_template('companion/index.html')

@companion_bp.route('/chat', methods=['POST'])
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
