import multiprocessing
import os

# Gunicorn config variables
workers = 1  # Single worker for free tier
worker_class = "gevent"
worker_connections = 50  # Reduced connections for free tier
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
timeout = 30  # Reduced timeout
keepalive = 2  # Reduced keepalive
max_requests = 250  # Reduced max requests
max_requests_jitter = 25

# Memory management
worker_tmp_dir = "/dev/shm"  # Use memory for temp files
forwarded_allow_ips = "*"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Prevent gevent monkey-patching warning
preload_app = True
