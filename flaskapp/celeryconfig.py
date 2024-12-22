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
broker_connection_retry = True
broker_connection_retry_on_startup = True
broker_connection_max_retries = None  # Retry forever
broker_connection_timeout = 30  # 30 seconds connection timeout

# Broker Pool Settings
broker_pool_limit = 10  # Limit to 10 connections in the pool
broker_heartbeat = 10  # Send heartbeat every 10 seconds
broker_heartbeat_checkrate = 2.0  # Check for heartbeat twice per second

# Redis visibility timeout (how long tasks are reserved for)
broker_transport_options = {
    'visibility_timeout': 43200,  # 12 hours
    'socket_timeout': 30,  # 30 seconds socket timeout
    'socket_connect_timeout': 30,  # 30 seconds connect timeout
    'socket_keepalive': True,  # Enable TCP keepalive
    'health_check_interval': 10,  # Check connection health every 10 seconds
}

# Result backend settings
result_backend_transport_options = broker_transport_options.copy()
