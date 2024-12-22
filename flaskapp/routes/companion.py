import os
import base64
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user, login_required
import google.generativeai as genai
from datetime import datetime

companion_bp = Blueprint('companion', __name__, url_prefix='/companion')

# Configure Google Generative AI
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-exp-1206')

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

        # Start async chat task
        from ..tasks import process_companion_chat
        from ..rq_app import q
        task = q.enqueue(process_companion_chat, user_message, current_user.firebase_uid, request_id)
        
        return jsonify({
            'message': 'Task enqueued',
            'request_id': request_id,
            'task_id': task.id
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
