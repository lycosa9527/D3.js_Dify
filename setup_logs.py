#!/usr/bin/env python3
"""
MindGraph Logs Directory Setup Script
Creates the logs directory and sets proper permissions for Waitress logging.
Run this script before starting the server on any platform.
"""

import os
import sys
import stat

def setup_logs_directory():
    """Create logs directory and set proper permissions"""
    print("🔧 Setting up MindGraph logs directory...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "logs")
    
    print(f"📁 Script directory: {script_dir}")
    print(f"📁 Logs directory: {logs_dir}")
    
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, mode=0o755)
            print(f"✅ Created logs directory: {logs_dir}")
        else:
            print(f"📁 Logs directory already exists: {logs_dir}")
        
        # Create log files if they don't exist
        log_files = [
            "waitress_access.log",
            "waitress_error.log", 
            "waitress.pid",
            "app.log",
            "agent.log"
        ]
        
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            if not os.path.exists(log_path):
                # Create empty log file
                with open(log_path, 'w') as f:
                    pass
                print(f"📝 Created log file: {log_file}")
            else:
                print(f"📝 Log file exists: {log_file}")
        
        # Set proper permissions (755 for directory, 644 for files)
        os.chmod(logs_dir, 0o755)
        print(f"🔐 Set directory permissions: {oct(os.stat(logs_dir).st_mode)[-3:]}")
        
        # Set file permissions
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            if os.path.isfile(log_path):
                os.chmod(log_path, 0o644)
                print(f"🔐 Set file permissions for {log_file}: {oct(os.stat(log_path).st_mode)[-3:]}")
        
        print("\n✅ Logs directory setup completed successfully!")
        print(f"📁 You can now run: python run_server.py")
        
    except Exception as e:
        print(f"❌ Error setting up logs directory: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_logs_directory()
