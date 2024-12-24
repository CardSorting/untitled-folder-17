import os
from flask import current_app
from celery import Celery
from flaskapp import create_app

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Configure Celery
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['REDIS_URL'],
        broker_connection_retry_on_startup=True,
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
    )
    
    # Update with any additional Flask config
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Initialize Flask app and Celery
flask_app = create_app()
celery_app = make_celery(flask_app)

# Register tasks from modules
from .tasks import chat_tasks, companion_tasks

# Register chat tasks
chat_task_registry = chat_tasks.register_tasks(celery_app)
process_chat_message = chat_task_registry['process_chat_message']

# Register companion tasks
companion_task_registry = companion_tasks.register_tasks(celery_app)
process_companion_chat = companion_task_registry['process_companion_chat']
