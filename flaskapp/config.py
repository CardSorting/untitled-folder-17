import os
import json
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis and Celery settings
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://default:dkEQtmoDlghnUbFOpyLLRMtWOuutVuNC@junction.proxy.rlwy.net:51904')
    CHAT_REDIS_URL = os.environ.get('CHAT_REDIS_URL', REDIS_URL)
    CELERY_BROKER_URL = REDIS_URL
    broker_url = REDIS_URL
    result_backend = REDIS_URL
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    broker_connection_retry_on_startup = True
    CELERY_TASK_ROUTES = {
        'flaskapp.tasks.companion_tasks.process_companion_chat_task': {'queue': 'default'},
        'flaskapp.tasks.process_chat_message_task': {'queue': 'chat'}
    }

    # Firebase Admin SDK settings
    FIREBASE_CREDENTIALS_PATH = os.path.join(os.path.dirname(basedir), 'firebase-credentials.json')
    FIREBASE_CREDENTIALS = None
    
    # Try to load Firebase credentials from environment variable
    firebase_creds_str = os.environ.get('FIREBASE_CREDENTIALS_JSON')
    if firebase_creds_str:
        try:
            FIREBASE_CREDENTIALS = json.loads(firebase_creds_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing FIREBASE_CREDENTIALS_JSON: {e}")
    
    # If not in environment, try to load from file
    if not FIREBASE_CREDENTIALS and FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
        try:
            with open(FIREBASE_CREDENTIALS_PATH, 'r') as f:
                FIREBASE_CREDENTIALS = json.load(f)
        except Exception as e:
            print(f"Error loading Firebase credentials from file: {e}")

    # Firebase Web SDK settings
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')

    # Google AI settings
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

    @staticmethod
    def now():
        return datetime.utcnow()
