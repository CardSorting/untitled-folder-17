from .celery_app import celery
from .utils.backblaze import b2_client
from datetime import datetime
import base64

@celery.task(bind=True, name='upload_audio_to_b2', max_retries=3)
def upload_audio_to_b2(self, audio_base64, user_id, request_id):
    """Upload audio to Backblaze B2 as a background task"""
    try:
        # Remove data URL prefix if present
        if 'base64,' in audio_base64:
            audio_base64 = audio_base64.split('base64,')[1]
        
        # Decode base64 audio data
        audio_data = base64.b64decode(audio_base64)
        
        # Upload to B2
        result = b2_client.upload_audio(audio_data, user_id)
        
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

@celery.task
def process_audio_upload(audio_base64, user_id, request_id):
    """Process audio upload with retry mechanism"""
    try:
        # Start upload task
        upload_task = upload_audio_to_b2.delay(audio_base64, user_id, request_id)
        
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
