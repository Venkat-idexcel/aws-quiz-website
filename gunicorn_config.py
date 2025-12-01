# Gunicorn Configuration for Quiz Website Production Deployment
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
backlog = 2048

# Worker processes - Optimized for high load
# Using gevent for async handling - can support thousands of concurrent connections
# Target capacity: 1000+ concurrent connections
workers = int(os.getenv('GUNICORN_WORKERS', 16))  # Increased to 16 workers for very high concurrency
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gevent')
# Number of concurrent clients per worker (gevent/eventlet) - significantly increased
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', 5000))  # 5000 connections per worker
# Restart workers periodically to avoid memory growth
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 5000))  # Increased before restart
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 200))  # More jitter for load balancing

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 5000  # Increased for better performance
max_requests_jitter = 200  # More jitter for load distribution

# Timeout - optimized for high load
timeout = 120  # Increased timeout for slow connections
keepalive = 5  # Reduced keepalive to free up connections faster

# Security - increased limits for better performance
limit_request_line = 8192  # Increased for larger requests
limit_request_fields = 200  # More fields allowed
limit_request_field_size = 16384  # Larger field sizes

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