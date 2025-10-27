# Gunicorn Configuration for Quiz Website Production Deployment
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
backlog = 2048

# Worker processes
# Calculate workers conservatively: (2 x CPU) + 1 is a good baseline for sync workers.
# For gevent (async) we can run fewer OS processes and rely on concurrency via greenlets.
# Target capacity: ~200 concurrent connections. With gevent worker_connections=1000,
# a small number of workers can handle many concurrent clients; tune per-instance CPU/RAM.
workers = int(os.getenv('GUNICORN_WORKERS', 8))  # 8 workers for high concurrency
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gevent')
# Number of concurrent clients per worker (gevent/eventlet)
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', 2000))  # 2000 connections per worker
# Restart workers periodically to avoid memory growth
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 2000))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 100))

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 30
keepalive = 60

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'quiz_website'

# Server mechanics
preload_app = True
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Hook functions
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Quiz Website server is ready. Listening on: %s", server.address)

def worker_int(worker):
    """Called just after a worker has been interrupted."""
    worker.log.info("Worker received INT or QUIT signal")

def on_exit(server):
    """Called just before the server is shut down."""
    server.log.info("Quiz Website server is shutting down")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)