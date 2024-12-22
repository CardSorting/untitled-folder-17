# Imports
imports = ['flaskapp.tasks']

import ssl

# Redis configuration
broker_url = 'rediss://default:AZu8AAIjcDE4ZWYwN2QyYmFkZDk0NDQxODBjOGJlYjI3MmQ3ZjNjMnAxMA@amused-bee-39868.upstash.io:6379/0'
result_backend = broker_url

# SSL settings for Redis
broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE,
    'ssl_ca_certs': None,
    'ssl_certfile': None,
    'ssl_keyfile': None
}
redis_backend_use_ssl = broker_use_ssl

# Serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

# Task settings
task_track_started = True
task_time_limit = 30 * 60  # 30 minutes
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50

# Time settings
timezone = 'UTC'
enable_utc = True

# Connection settings
broker_connection_retry_on_startup = True
