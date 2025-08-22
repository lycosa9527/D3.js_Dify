#!/usr/bin/env python3
"""
Debug Gunicorn startup issues
Run this to see exactly what's happening when Gunicorn starts
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    print("🐛 Debugging Gunicorn Startup Issues")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env loaded
    qwen_key = os.getenv('QWEN_API_KEY')
    if qwen_key:
        print(f"✅ QWEN_API_KEY loaded: {'*' * min(len(qwen_key), 8)}...")
    else:
        print("❌ QWEN_API_KEY not found")
        return
    
    # Check if gunicorn is installed
    try:
        import gunicorn
        print(f"✅ Gunicorn version: {gunicorn.__version__}")
    except ImportError:
        print("❌ Gunicorn not installed")
        return
    
    # Check if app.py can be imported
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        print("✅ Flask app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Flask app: {e}")
        return
    
    # Test 1: Basic Gunicorn without config
    print("\n🔧 Test 1: Basic Gunicorn (no config)")
    try:
        cmd = [sys.executable, '-m', 'gunicorn', '--bind', '127.0.0.1:9527', '--workers', '1', '--timeout', '30', '--log-level', 'debug', 'app:app']
        print(f"Running: {' '.join(cmd)}")
        
        # Run with output capture to see what happens
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Basic Gunicorn started successfully")
        else:
            print(f"❌ Basic Gunicorn failed with code {result.returncode}")
            if result.stdout:
                print(f"stdout: {result.stdout}")
            if result.stderr:
                print(f"stderr: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        print("✅ Basic Gunicorn started successfully (timeout reached)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Gunicorn with minimal config
    print("\n🔧 Test 2: Gunicorn with minimal config")
    try:
        cmd = [sys.executable, '-m', 'gunicorn', '--config', 'gunicorn.conf.py', 'app:app']
        print(f"Running: {' '.join(cmd)}")
        
        # Run with output capture to see what happens
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Gunicorn with config started successfully")
        else:
            print(f"❌ Gunicorn with config failed with code {result.returncode}")
            if result.stdout:
                print(f"stdout: {result.stdout}")
            if result.stderr:
                print(f"stderr: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        print("✅ Gunicorn with config started successfully (timeout reached)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check if logs directory exists and is writable
    print("\n🔧 Test 3: Check logs directory")
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        print(f"✅ Logs directory exists: {logs_dir}")
        try:
            test_file = os.path.join(logs_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("✅ Logs directory is writable")
        except Exception as e:
            print(f"❌ Logs directory is not writable: {e}")
    else:
        print(f"❌ Logs directory does not exist: {logs_dir}")
        try:
            os.makedirs(logs_dir, exist_ok=True)
            print(f"✅ Created logs directory: {logs_dir}")
        except Exception as e:
            print(f"❌ Failed to create logs directory: {e}")
    
    print("\n" + "=" * 50)
    print("Debug completed!")

if __name__ == '__main__':
    main()
