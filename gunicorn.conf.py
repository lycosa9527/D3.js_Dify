# Minimal Gunicorn Configuration for MindGraph
# This configuration focuses on stability and basic functionality

# Server socket
bind = "0.0.0.0:9527"
workers = 1
worker_class = "sync"
timeout = 120

# Logging - log to console for debugging
loglevel = "debug"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Basic settings
preload_app = False
daemon = False

# Environment variables
raw_env = [
    'MINDGRAPH_ENV=production',
    'PYTHONUNBUFFERED=1',
]
