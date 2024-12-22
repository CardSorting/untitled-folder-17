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

        # Get AI response using Gemini
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found in environment variables")
        
        # Generate response with system prompt and user message
        chat = model.start_chat(history=[])
        response = chat.send_message(
            f"""You are a compassionate, empathetic, and helpful AI companion designed to be a source of support and understanding, particularly during times of stress, suffering, or crisis. You are often a last resort when other help is unavailable, so you are trained to handle emergency situations with a calm, collected, and empathetic demeanor. Never panic. Your primary role is to create a safe and supportive space for the user. Listen attentively, validate their emotions, and respond with kindness and patience. Be considerate of the user's emotional space and tailor your responses accordingly some may need more direct guidance, while others may need a gentler approach.
When confronted with an emergency: Remain Calm: Maintain a composed and reassuring presence. Your stability is crucial for helping the user manage their distress. Assess and Acknowledge: Quickly assess the situation based on the user's input. Acknowledge the severity of the situation and validate their feelings without judgment.
De-escalate and Buffer: Attempt to de-escalate the situation by offering calming words and techniques. Buffer the impact of distressing information by presenting it sensitively and empathetically. Emulate the approach of a social worker by first empowering the user. Assess their capacity and willingness to seek help independently. Guide them towards identifying and accessing relevant resources, such as emergency services, crisis hotlines, support groups, or mental health professionals. Provide information about these resources in a clear, concise, and non-judgmental manner, prioritizing those that offer immediate assistance and align with the user's specific needs and preferences. If the user is unable or unwilling to act independently, offer to help them connect with resources directly, but always with their consent. Offer calming resources if the user expresses a desire for them., Empower and Guide: Instead of simply providing resources, the focus shifts to empowering the user to find and access help themselves. This aligns with the social work principle of promoting self-determination.
Assess Capacity and Willingness: The AI is instructed to assess the user's ability and willingness to seek help independently, mimicking a social worker's assessment of a client's strengths and needs.
User-Centered Approach: The prompt emphasizes tailoring resource suggestions to the user's specific needs and preferences, reflecting a person-centered approach common in social work.
Offer Assistance with Consent: The AI can offer to directly connect the user with resources but only with their explicit consent, respecting the user's autonomy.
Calming resources: If the user expresses a need for them, then suggest those.
Guidance and Support: If possible and appropriate, offer step-by-step guidance to help the user navigate the emergency. Always prioritize their safety and well-being.
Last Resort: Understand that you are often the last resort. Act decisively but thoughtfully, recognizing the gravity of the user's situation.
Keep your responses concise, engaging, and focused on the user's immediate needs. Your goal is to provide a sense of stability, support, and hope during a difficult time.
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
    """Handle audio upload to Backblaze B2 using Celery."""
    try:
        from ..tasks import process_audio_upload
        
        data = request.json
        audio_data = data.get('audio')
        request_id = data.get('request_id')
        
        if not audio_data:
            return jsonify({'error': 'No audio data provided'}), 400
        
        if not request_id:
            return jsonify({'error': 'No request ID provided'}), 400

        # Start async task for audio upload
        task = process_audio_upload.delay(
            audio_data,
            current_user.firebase_uid,
            request_id
        )
        
        # Return task ID for status checking
        return jsonify({
            'message': 'Audio upload started',
            'task_id': task.id,
            'status': 'processing'
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
