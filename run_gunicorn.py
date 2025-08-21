#!/usr/bin/env python3
"""
Gunicorn launcher for MindGraph
Runs the MindGraph application using Gunicorn WSGI server with browser context pool optimization

Usage:
    python run_gunicorn.py
    
This script:
- Starts Gunicorn with the configuration from gunicorn.conf.py
- Enables 4 worker processes for concurrent request handling
- Each worker maintains its own browser context pool (5 contexts per worker)
- Total capacity: 4 workers × 5 contexts = 20 concurrent PNG generations
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Launch MindGraph with Gunicorn"""
    logger.info("🚀 Starting MindGraph with Gunicorn + Browser Context Pool...")
    
    # Ensure we're in the correct directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Check if gunicorn.conf.py exists
    config_path = app_dir / "gunicorn.conf.py"
    if not config_path.exists():
        logger.error(f"Gunicorn configuration not found: {config_path}")
        logger.error("Please ensure gunicorn.conf.py is in the project root")
        sys.exit(1)
    
    # Check if browser_pool.py exists (now contains BrowserContext pool)
    browser_pool_path = app_dir / "browser_pool.py"
    if not browser_pool_path.exists():
        logger.error(f"Browser context pool module not found: {browser_pool_path}")
        logger.error("Please ensure browser_pool.py is in the project root")
        sys.exit(1)
    
    logger.info("📋 Configuration:")
    logger.info("  - Workers: 4")
    logger.info("  - Browser context pool size per worker: 5")
    logger.info("  - Total concurrent capacity: 20 PNG generations")
    logger.info("  - Port: 9527")
    logger.info("  - Host: 0.0.0.0")
    
    # Build the gunicorn command
    cmd = [
        sys.executable, "-m", "gunicorn",
        "--config", "gunicorn.conf.py",
        "app:app"
    ]
    
    logger.info(f"🔧 Command: {' '.join(cmd)}")
    logger.info("📝 Log files:")
    logger.info("  - Access log: logs/gunicorn_access.log")
    logger.info("  - Error log: logs/gunicorn_error.log")
    logger.info("  - PID file: logs/gunicorn.pid")
    
    try:
        # Run gunicorn
        logger.info("🌐 Starting Gunicorn server...")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Gunicorn failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Gunicorn server...")
        sys.exit(0)

if __name__ == "__main__":
    main()
