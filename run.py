
import subprocess
import threading
import os
from flaskapp import create_app

def start_celery_worker():
    # Kill existing Celery workers
    subprocess.run(['pkill', '-f', 'celery'])
    
    # Start new worker
    subprocess.run([
        'celery', '-A', 'flaskapp.celery_app', 'worker',
        '--loglevel=info', '--concurrency=1',
        '--without-gossip', '--without-mingle',
        '--without-heartbeat'
    ])

def run_app():
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    # Start Celery worker in a separate thread
    celery_thread = threading.Thread(target=start_celery_worker)
    celery_thread.daemon = True
    celery_thread.start()
    
    # Run Flask app
    run_app()
