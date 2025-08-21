# Gunicorn Configuration for MindGraph
# Production WSGI deployment with Browser Context Pool per Worker
# 
# This configuration enables:
# - 4 worker processes for concurrent request handling
# - Each worker has its own browser context pool (5 contexts per worker)
# - Total capacity: 4 workers × 5 contexts = 20 concurrent PNG generations
# - WSGI compliance for production deployment

import multiprocessing
import os

# Get the directory where this config file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Server socket
bind = "0.0.0.0:9527"  # Using default MindGraph API port
backlog = 2048

# Worker processes
workers = 4  # 4 worker processes for optimal concurrency
worker_class = "sync"  # Sync workers work best with Playwright
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # Don't preload - let each worker initialize its own browser context pool

# Timeout settings
timeout = 120  # 2 minutes for complex diagram generation
keepalive = 2
graceful_timeout = 30

# Logging - Use absolute paths to avoid FileNotFoundError
loglevel = "info"
accesslog = os.path.join(BASE_DIR, "logs", "gunicorn_access.log")
errorlog = os.path.join(BASE_DIR, "logs", "gunicorn_error.log")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'mindgraph_api'

# Server mechanics
daemon = False
pidfile = os.path.join(BASE_DIR, "logs", "gunicorn.pid")
user = None
group = None
tmp_upload_dir = None

# SSL (for production HTTPS)
# keyfile = None
# certfile = None

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting MindGraph API server with Gunicorn...")

def on_reload(server):
    """Called to recycle workers during a reload."""
    server.log.info("Reloading MindGraph API workers...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("MindGraph API server is ready. Workers: %s", workers)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker %s interrupted", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker %s spawned (pid: %s)", worker.age, worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    worker.log.info("Worker %s ready with browser context pool initialization", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker %s aborted", worker.pid)

# Environment variables for worker processes
raw_env = [
    'MINDGRAPH_ENV=production',
    'GUNICORN_WORKER=true',
]

# Performance tuning
max_requests = 1000  # Restart worker after 1000 requests to prevent memory leaks
max_requests_jitter = 100  # Add randomness to prevent thundering herd

# Memory and file limits
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Development vs Production settings
if os.getenv('MINDGRAPH_ENV') == 'development':
    workers = 2  # Fewer workers for development
    loglevel = 'debug'
    reload = True
    reload_extra_files = ['templates/', 'static/']
else:
    # Production optimizations
    workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
    preload_app = False  # Browser context pools need per-worker initialization
