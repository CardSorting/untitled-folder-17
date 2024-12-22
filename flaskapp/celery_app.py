from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

def create_celery():
    celery = Celery(
        'flaskapp',
        broker=os.environ.get('CELERY_BROKER_URL'),
        backend=os.environ.get('CELERY_RESULT_BACKEND'),
        include=['flaskapp.tasks']
    )

    # Optional configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        worker_prefetch_multiplier=1,  # One task per worker at a time
        worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    )

    return celery

celery = create_celery()
