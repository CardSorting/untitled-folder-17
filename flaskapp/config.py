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
    REDIS_URL = 'redis://matrixvv-oo6rj9.serverless.usw2.cache.amazonaws.com:6379'
    CHAT_REDIS_URL = 'redis://matrixmm-oo6rj9.serverless.usw2.cache.amazonaws.com:6379'
    CELERY_BROKER_URL = REDIS_URL
    result_backend = REDIS_URL
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    broker_connection_retry_on_startup = True  # Add this to handle the broker connection retry warning
    CELERY_TASK_ROUTES = {
        'flaskapp.tasks.process_companion_chat': {'queue': 'default'},
        'flaskapp.tasks.process_chat_message': {'queue': 'chat'}
    }

    # Firebase Admin SDK settings
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH') or \
        os.path.join(basedir, '..', 'cred', 'irlmbm-firebase-adminsdk-p4dxq-35e9808542.json')

    # Load Firebase Web SDK config from credentials file
    try:
        with open(FIREBASE_CREDENTIALS_PATH) as f:
            cred_data = json.load(f)
            project_id = cred_data.get('project_id', '')
            
            # Firebase Web SDK settings
            FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
            FIREBASE_AUTH_DOMAIN = f"{project_id}.firebaseapp.com"
            FIREBASE_PROJECT_ID = project_id
            FIREBASE_STORAGE_BUCKET = f"{project_id}.appspot.com"
            FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
            FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')
    except Exception as e:
        print(f"Warning: Could not load Firebase credentials: {e}")
        # Set empty defaults
        FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
        FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
        FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
        FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
        FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
        FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')

    @staticmethod
    def now():
        return datetime.utcnow()
