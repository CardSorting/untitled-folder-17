import os
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from datetime import datetime
from flask import current_app

class BackblazeB2:
    def __init__(self):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.key_id = os.environ.get('B2_KEY_ID')
        self.application_key = os.environ.get('B2_APPLICATION_KEY')
        self.bucket_name = os.environ.get('B2_BUCKET_NAME')
        
        if not all([self.key_id, self.application_key, self.bucket_name]):
            raise ValueError("Missing required Backblaze B2 environment variables")
            
        self._authorize()

    def _authorize(self):
        """Authorize with Backblaze B2"""
        self.api.authorize_account("production", self.key_id, self.application_key)
        self.bucket = self.api.get_bucket_by_name(self.bucket_name)

    def upload_audio(self, audio_data, user_id):
        """Upload audio data to Backblaze B2"""
        try:
            # Generate a unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"audio/{user_id}/{timestamp}.webm"

            # Upload the file
            self.bucket.upload_bytes(
                data_bytes=audio_data,
                file_name=filename,
                content_type='audio/webm',
                file_info={
                    'user_id': user_id,
                    'timestamp': timestamp
                }
            )

            # Get the file URL
            file_url = f"https://f005.backblazeb2.com/file/{self.bucket_name}/{filename}"
            return {
                'success': True,
                'url': file_url,
                'filename': filename
            }

        except Exception as e:
            current_app.logger.error(f"Error uploading to B2: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_user_recordings(self, user_id, max_files=100):
        """List all recordings for a user"""
        try:
            files = []
            for file_info, _ in self.bucket.ls(f"audio/{user_id}/", max_entries=max_files):
                files.append({
                    'filename': file_info.file_name,
                    'url': f"https://f005.backblazeb2.com/file/{self.bucket_name}/{file_info.file_name}",
                    'uploaded': file_info.upload_timestamp,
                    'size': file_info.size
                })
            return {
                'success': True,
                'files': files
            }
        except Exception as e:
            current_app.logger.error(f"Error listing B2 files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Create a singleton instance
b2_client = BackblazeB2()
