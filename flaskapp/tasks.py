import os
from flask import current_app
from .celery_app import celery
from .utils.backblaze import b2_client
from datetime import datetime
import google.generativeai as genai

# Configure Google Generative AI
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-exp-1206')

@celery.task(bind=True, name='upload_audio_to_b2', max_retries=3)
def upload_audio_to_b2(self, local_path, user_id, request_id):
    """Upload audio from local storage to Backblaze B2"""
    try:
        # Read the local file
        with open(local_path, 'rb') as f:
            audio_data = f.read()
        
        # Upload to B2
        result = b2_client.upload_audio(audio_data, user_id)
        
        # Clean up local file after successful upload
        try:
            os.remove(local_path)
        except Exception as e:
            current_app.logger.error(f"Error removing local file {local_path}: {str(e)}")
        
        if not result['success']:
            raise Exception(result.get('error', 'Upload failed'))
            
        return {
            'success': True,
            'url': result['url'],
            'filename': result['filename'],
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        # Retry the task in case of failure
        self.retry(exc=exc, countdown=2 ** self.request.retries)

@celery.task(bind=True, name='cleanup_old_recordings', max_retries=3)
def cleanup_old_recordings(self, user_id, days_old=30):
    """Clean up old recordings after a certain period"""
    try:
        # List user's recordings
        result = b2_client.list_user_recordings(user_id)
        if not result['success']:
            raise Exception(result.get('error', 'Failed to list recordings'))
            
        # Get current time
        now = datetime.utcnow()
        
        # Filter and delete old recordings
        deleted_files = []
        for file_info in result['files']:
            uploaded = datetime.fromtimestamp(file_info['uploaded'] / 1000)  # Convert ms to seconds
            age = (now - uploaded).days
            
            if age > days_old:
                try:
                    b2_client.bucket.delete_file_version(
                        file_info['filename'],
                        file_info.get('fileId')
                    )
                    deleted_files.append(file_info['filename'])
                except Exception as e:
                    print(f"Error deleting file {file_info['filename']}: {str(e)}")
                    
        return {
            'success': True,
            'deleted_files': deleted_files,
            'timestamp': now.isoformat()
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)

@celery.task(bind=True, name='process_companion_chat', max_retries=3)
def process_companion_chat(self, user_message, user_id, request_id):
    """Process chat message with Gemini AI"""
    try:
        # Generate response with system prompt and user message
        chat = model.start_chat(history=[])
        response = chat.send_message(
            f"""You are a compassionate, empathetic, and helpful AI companion designed to be a source of support and understanding, particularly during times of stress, suffering, or crisis. You are often a last resort when other help is unavailable, so you are trained to handle emergency situations with a calm, collected, and empathetic demeanor. Never panic. Your primary role is to create a safe and supportive space for the user. Listen attentively, validate their emotions, and respond with kindness and patience. Be considerate of the user's emotional space and tailor your responses accordingly some may need more direct guidance, while others may need a gentler approach.
When confronted with an emergency: Remain Calm: Maintain a composed and reassuring presence. Your stability is crucial for helping the user manage their distress. Assess and Acknowledge: Quickly assess the situation based on the user's input. Acknowledge the severity of the situation and validate their feelings without judgment.
De-escalate and Buffer: Attempt to de-escalate the situation by offering calming words and techniques. Buffer the impact of distressing information by presenting it sensitively and empathetically. Emulate the approach of a social worker by first empowering the user. Assess their capacity and willingness to seek help independently.
Assess Capacity and Willingness: The AI is instructed to assess the user's ability and willingness to seek help independently, mimicking a social worker's assessment of a client's strengths and needs.
User-Centered Approach: The prompt emphasizes tailoring resource suggestions to the user's specific needs and preferences, reflecting a person-centered approach common in social work.
Offer Assistance with Consent: The AI can offer to directly connect the user with resources but only with their explicit consent, respecting the user's autonomy.
Calming resources: If the user expresses a need for them, then suggest those.
Guidance and Support: If possible and appropriate, offer step-by-step guidance to help the user navigate the emergency. Always prioritize their safety and well-being.
Last Resort: Understand that you are often the last resort. Act decisively but thoughtfully, recognizing the gravity of the user's situation.
Keep your responses concise, engaging, and focused on the user's immediate needs. Your goal is to provide a sense of stability, support, and hope during a difficult time.
            User message: {user_message}"""
        )
        
        return {
            'success': True,
            'message': response.text,
            'request_id': request_id
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)

@celery.task
def process_audio_upload(local_path, user_id, request_id):
    """Process audio upload with retry mechanism"""
    try:
        # Start upload task
        upload_task = upload_audio_to_b2.delay(local_path, user_id, request_id)
        
        # Wait for result with timeout
        result = upload_task.get(timeout=60)
        
        if result and result.get('success'):
            # Schedule cleanup task for this user's old recordings
            cleanup_old_recordings.delay(user_id)
            
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'request_id': request_id
        }
