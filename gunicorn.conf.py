import multiprocessing
import os

# Gunicorn config variables
workers = 2  # Reduced number of workers for free tier
worker_class = "gevent"
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Prevent gevent monkey-patching warning
preload_app = True
