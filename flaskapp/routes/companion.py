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
        task = process_companion_chat.delay(user_message, current_user.firebase_uid, request_id)
        
        # Wait for result with timeout
        result = task.get(timeout=60)
        
        if result and result.get('success'):
            ai_message = result['message']
            # Save message to Firestore
            current_user.save_message(user_message, ai_message, request_id)
            
            return jsonify({
                'message': ai_message,
                'request_id': request_id
            })
        else:
            raise Exception(result.get('error', 'Chat processing failed'))

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
    """Handle audio blob upload to local storage and B2."""
    try:
        from ..tasks import process_audio_upload
        import os
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        request_id = request.form.get('request_id')
        
        if not request_id:
            return jsonify({'error': 'No request ID provided'}), 400
            
        # Save audio blob locally first
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{current_user.firebase_uid}_{timestamp}.webm"
        local_path = os.path.join('flaskapp/static/audio_blobs', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Save the file
        audio_file.save(local_path)
        
        # Start async task for B2 upload
        task = process_audio_upload.delay(
            local_path,
            current_user.firebase_uid,
            request_id
        )
        
        return jsonify({
            'message': 'Audio upload started',
            'task_id': task.id,
            'status': 'processing',
            'local_path': local_path
        })

    except Exception as e:
        current_app.logger.error(f"Error starting audio upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@companion_bp.route('/upload-status/<task_id>', methods=['GET'])
@login_required
def upload_status(task_id):
    """Check the status of an audio upload task."""
    from ..celery_app import celery
    
    try:
        task_result = celery.AsyncResult(task_id)
        
        if task_result.ready():
            result = task_result.get()
            if result.get('success'):
                # Save audio URL to user's chat history in Firestore
                current_user.save_message(
                    user_message="[Audio Message]",
                    ai_response="",
                    request_id=result.get('request_id', ''),
                    audio_url=result.get('url')
                )
                return jsonify({
                    'status': 'completed',
                    'result': result
                })
            else:
                return jsonify({
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }), 500
        else:
            return jsonify({
                'status': 'processing',
                'state': task_result.state
            })
            
    except Exception as e:
        current_app.logger.error(f"Error checking upload status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

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
