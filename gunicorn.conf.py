# Gunicorn Configuration for MindGraph
# Production WSGI deployment with Browser Context Pool per Worker

import multiprocessing
import os
import platform

# Get the directory where this config file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Server socket
bind = "0.0.0.0:9527"  # Using default MindGraph API port
backlog = 2048

# Worker processes - simplified for stability
workers = 2  # Start with fewer workers for stability
worker_class = "sync"  # Sync workers work best with Playwright
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # Don't preload - let each worker initialize its own browser context pool

# Platform-specific optimizations
if platform.system().lower() == 'linux':
    worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance on Linux
else:
    worker_tmp_dir = None  # Use system default on other platforms

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

# Environment variables for worker processes
raw_env = [
    'MINDGRAPH_ENV=production',
    'GUNICORN_WORKER=true',
    'PYTHONUNBUFFERED=1',
]

# Memory and file limits
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
