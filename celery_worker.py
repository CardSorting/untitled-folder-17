from dotenv import load_dotenv
from flaskapp.celery_app import celery

load_dotenv()

if __name__ == '__main__':
    celery.worker_main([
        'worker',
        '--loglevel=info',
        '--pool=prefork',
        '--concurrency=4',
        '--max-tasks-per-child=50',
        '--max-memory-per-child=512000',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat'
    ])
