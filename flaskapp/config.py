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

    # Redis settings
    REDIS_URL = 'redis://default:aPgEdkFGdTOBJtLJJMQEApZKyYsUDcNm@junction.proxy.rlwy.net:54156'

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
