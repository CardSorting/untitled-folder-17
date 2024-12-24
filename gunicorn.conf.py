import multiprocessing

# Gunicorn config variables
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
bind = "0.0.0.0:$PORT"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
