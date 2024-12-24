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
        broker_connection_max_retries=100,
        broker_connection_timeout=30,
        broker_heartbeat=None,
        broker_pool_limit=None,
        redis_max_connections=None,
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
            'socket_timeout': 30,
            'socket_connect_timeout': 30,
            'socket_keepalive': True
        },
        redis_retry_on_timeout=True,
        redis_socket_timeout=30,
        redis_socket_connect_timeout=30,
        redis_socket_keepalive=True
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
