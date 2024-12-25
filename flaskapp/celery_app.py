from celery import Celery
from . import create_app

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Configure Celery with robust Redis settings
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['REDIS_URL'],
        broker_connection_retry=True,
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=10,
        broker_connection_timeout=10,
        worker_prefetch_multiplier=1,
        worker_concurrency=2,
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        task_time_limit=300,
        task_soft_time_limit=60,
        worker_disable_rate_limits=True,
        broker_transport_options={
            'visibility_timeout': 1800,
            'socket_timeout': 10,
            'socket_connect_timeout': 10
        }
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
