#!/usr/bin/env python3
"""
Simple environment variable checker for MindGraph
Run this on your Ubuntu server to verify environment setup
"""

import os
from dotenv import load_dotenv

def main():
    print("🔍 MindGraph Environment Checker")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ .env file found: {env_file}")
        
        # Load .env file
        load_dotenv()
        print("✅ .env file loaded successfully")
        
        # Check file permissions
        stat = os.stat(env_file)
        print(f"📁 File permissions: {oct(stat.st_mode)[-3:]}")
        
        # Read and display .env content (masked)
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
                print(f"📝 .env file contains {len(lines)} lines")
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if 'KEY' in key.upper() or 'SECRET' in key.upper():
                                masked_value = '*' * min(len(value), 8) + '...' if len(value) > 8 else '*' * len(value)
                                print(f"   {key}={masked_value}")
                            else:
                                print(f"   {key}={value}")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print(f"❌ .env file not found: {env_file}")
    
    print("\n🌍 Environment Variables:")
    print("-" * 40)
    
    # Check critical variables
    critical_vars = ['QWEN_API_KEY', 'QWEN_API_URL', 'MINDGRAPH_ENV']
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var.upper() or 'SECRET' in var.upper():
                masked_value = '*' * min(len(value), 8) + '...' if len(value) > 8 else '*' * len(value)
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    print("\n🔧 Current Working Directory:")
    print(f"   {os.getcwd()}")
    
    print("\n📁 Directory Contents:")
    try:
        files = os.listdir('.')
        for file in sorted(files):
            if file.startswith('.'):
                print(f"   {file}")
    except Exception as e:
        print(f"   Error listing files: {e}")
    
    print("\n" + "=" * 40)
    print("Environment check completed!")

if __name__ == '__main__':
    main()
