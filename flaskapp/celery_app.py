from celery import Celery
from . import create_app

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
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = create_app()
celery = make_celery(flask_app)

# Import tasks to register them
from .tasks import companion_tasks
companion_tasks.register_tasks(celery)
