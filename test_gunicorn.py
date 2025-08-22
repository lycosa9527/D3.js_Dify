#!/usr/bin/env python3
"""
Test Gunicorn Configuration
Run this to test if Gunicorn can start with your configuration
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    print("🧪 Testing Gunicorn Configuration")
    print("=" * 40)
    
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
    
    # Test basic Gunicorn start (without config file first)
    print("\n🔧 Testing basic Gunicorn start...")
    try:
        cmd = [sys.executable, '-m', 'gunicorn', '--bind', '127.0.0.1:9527', '--workers', '1', '--timeout', '30', 'app:app']
        print(f"Running: {' '.join(cmd)}")
        
        # Start in background and wait a moment
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a few seconds to see if it starts
        import time
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Basic Gunicorn started successfully")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Basic Gunicorn failed")
            if stdout:
                print(f"stdout: {stdout.decode()}")
            if stderr:
                print(f"stderr: {stderr.decode()}")
            
    except Exception as e:
        print(f"❌ Error testing basic Gunicorn: {e}")
    
    # Test with minimal config file
    print("\n🔧 Testing Gunicorn with minimal config file...")
    try:
        cmd = [sys.executable, '-m', 'gunicorn', '--config', 'gunicorn_test.conf.py', 'app:app']
        print(f"Running: {' '.join(cmd)}")
        
        # Start in background and wait a moment
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a few seconds to see if it starts
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Gunicorn with minimal config started successfully")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Gunicorn with minimal config failed")
            if stdout:
                print(f"stdout: {stdout.decode()}")
            if stderr:
                print(f"stderr: {stderr.decode()}")
            
    except Exception as e:
        print(f"❌ Error testing Gunicorn with minimal config: {e}")
    
    # Test with original config file
    print("\n🔧 Testing Gunicorn with original config file...")
    try:
        cmd = [sys.executable, '-m', 'gunicorn', '--config', 'gunicorn.conf.py', 'app:app']
        print(f"Running: {' '.join(cmd)}")
        
        # Start in background and wait a moment
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a few seconds to see if it starts
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Gunicorn with original config started successfully")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Gunicorn with original config failed")
            if stdout:
                print(f"stdout: {stdout.decode()}")
            if stderr:
                print(f"stderr: {stderr.decode()}")
            
    except Exception as e:
        print(f"❌ Error testing Gunicorn with original config: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == '__main__':
    main()
