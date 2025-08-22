# Minimal Gunicorn Test Configuration
# This is a stripped-down version to test basic functionality

# Server socket
bind = "0.0.0.0:9527"
workers = 1
worker_class = "sync"
timeout = 30

# Logging
loglevel = "debug"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Basic settings
preload_app = False
daemon = False
