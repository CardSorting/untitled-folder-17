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
        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

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
        
        return jsonify({
            'message': ai_message
        })

    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
