import os
from dotenv import load_dotenv
from flaskapp.celery_app import celery

load_dotenv()

# Explicitly set broker and backend
celery.conf.broker_url = os.environ.get('CELERY_BROKER_URL')
celery.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND')

if __name__ == '__main__':
    celery.worker_main(['worker', '--loglevel=info', '--pool=solo'])
