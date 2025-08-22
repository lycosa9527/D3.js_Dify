#!/usr/bin/env python3
"""
MindGraph Platform-Aware Server Launcher
Automatically selects the appropriate WSGI server based on the platform:
- Windows: Waitress (pure Python, Windows-compatible)
- Linux/Unix: Gunicorn (production-grade, Unix-only)
"""

import os
import sys
import platform
import subprocess
import importlib.util

def check_package_installed(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system in ['linux', 'darwin']:  # Darwin is macOS
        return 'unix'
    else:
        return 'unknown'

def run_waitress():
    """Run MindGraph with Waitress (Windows)"""
    print("🟦 Starting MindGraph with Waitress (Windows environment)")
    
    if not check_package_installed('waitress'):
        print("❌ Waitress not installed. Install with: pip install waitress>=3.0.0")
        sys.exit(1)
    
    try:
        # Ensure we're in the correct directory (where this script is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        print(f"📁 Working directory: {os.getcwd()}")
        
        from waitress import serve
        from app import app
        
        # Load configuration
        config_module = {}
        with open('waitress.conf.py', 'r') as f:
            exec(f.read(), config_module)
        
        print(f"🚀 MindGraph starting on http://{config_module['host']}:{config_module['port']}")
        print(f"📋 Configuration: {config_module['threads']} threads, timeout: {config_module['channel_timeout']}s")
        
        serve(
            app, 
            host=config_module['host'], 
            port=config_module['port'],
            threads=config_module['threads'],
            cleanup_interval=config_module['cleanup_interval'],
            channel_timeout=config_module['channel_timeout'],
            send_bytes=config_module['send_bytes'],
            recv_bytes=config_module['recv_bytes']
        )
    except Exception as e:
        print(f"❌ Failed to start Waitress: {e}")
        sys.exit(1)

def run_gunicorn():
    """Run MindGraph with Gunicorn (Linux/Unix)"""
    print("🟩 Starting MindGraph with Gunicorn (Unix environment)")
    
    # Check system requirements for Gunicorn
    if platform.system().lower() == 'windows':
        print("⚠️  Warning: Gunicorn is not recommended on Windows")
        print("   Consider using Waitress instead: MINDGRAPH_SERVER=waitress python run_server.py")
    
    if not check_package_installed('gunicorn'):
        print("❌ Gunicorn not installed. Install with: pip install gunicorn>=21.2.0")
        sys.exit(1)
    
    try:
        # Ensure we're in the correct directory (where this script is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"📁 Logs directory: {os.path.join(os.getcwd(), 'logs')}")
        
        # Validate Gunicorn configuration file exists
        config_file = 'gunicorn.conf.py'
        if not os.path.exists(config_file):
            print(f"❌ Gunicorn configuration file not found: {config_file}")
            print("   Please ensure gunicorn.conf.py exists in the project root")
            sys.exit(1)
        
        # Check critical environment variables
        from dotenv import load_dotenv
        load_dotenv()  # Load .env file
        
        qwen_api_key = os.getenv('QWEN_API_KEY')
        if not qwen_api_key:
            print("❌ QWEN_API_KEY environment variable not set")
            print("   Please check your .env file or set the environment variable")
            print("   Example: export QWEN_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        print(f"✅ Environment variables loaded successfully")
        print(f"   QWEN_API_KEY: {'*' * min(len(qwen_api_key), 8)}...")
        
        # Use subprocess to run Gunicorn with configuration file
        cmd = [sys.executable, '-m', 'gunicorn', '--config', 'gunicorn.conf.py', 'app:app']
        print(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            # Run Gunicorn with better error capture
            print("🔍 Starting Gunicorn...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"❌ Gunicorn failed with exit code {result.returncode}")
                if result.stdout:
                    print(f"Gunicorn stdout: {result.stdout}")
                if result.stderr:
                    print(f"Gunicorn stderr: {result.stderr}")
                sys.exit(1)
            else:
                print("✅ Gunicorn started successfully")
                
        except subprocess.TimeoutExpired:
            print("✅ Gunicorn started successfully (timeout reached)")
        except subprocess.CalledProcessError as e:
            print(f"❌ Gunicorn failed with exit code {e.returncode}")
            print(f"Error details: {e}")
            if e.stdout:
                print(f"Gunicorn stdout: {e.stdout}")
            if e.stderr:
                print(f"Gunicorn stderr: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ Gunicorn not found. Install with: pip install gunicorn>=21.2.0")
            sys.exit(1)
        except KeyboardInterrupt:
            print("🛑 Gunicorn interrupted by user")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start Gunicorn: {e}")
        sys.exit(1)

def run_flask_dev():
    """Fallback: Run Flask development server"""
    print("🟨 Starting MindGraph with Flask development server (fallback)")
    print("⚠️  WARNING: This is not recommended for production use")
    
    try:
        subprocess.run([sys.executable, 'app.py'])
    except Exception as e:
        print(f"❌ Failed to start Flask development server: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("🎯 MindGraph Platform-Aware Server Launcher")
    print("=" * 50)
    
    # Detect platform
    current_platform = detect_platform()
    print(f"🖥️  Platform detected: {current_platform} ({platform.system()} {platform.release()})")
    
    # Check if force mode is specified
    force_server = os.getenv('MINDGRAPH_SERVER', '').lower()
    if force_server:
        print(f"🔧 Forced server mode: {force_server}")
    
    # Choose server based on platform or force mode
    if force_server == 'waitress':
        run_waitress()
    elif force_server == 'gunicorn':
        run_gunicorn()
    elif force_server == 'flask':
        run_flask_dev()
    elif current_platform == 'windows':
        run_waitress()
    elif current_platform == 'unix':
        run_gunicorn()
    else:
        print(f"⚠️  Unknown platform: {current_platform}, falling back to Flask development server")
        run_flask_dev()

if __name__ == '__main__':
    main()
