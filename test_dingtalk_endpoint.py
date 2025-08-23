#!/usr/bin/env python3
"""
Test script for the new DingTalk endpoint.
This script tests the /api/generate_dingtalk endpoint to ensure it returns
markdown format with temporary image URLs instead of PNG data.
Images are stored temporarily and automatically cleaned up after 24 hours.
"""

import requests
import json
import time

def test_dingtalk_endpoint():
    """Test the DingTalk endpoint with a simple prompt."""
    
    # Test configuration - use dynamic server URL
    try:
        from config import config
        base_url = config.SERVER_URL
    except ImportError:
        base_url = "http://localhost:9527"  # Fallback for testing
    endpoint = "/api/generate_dingtalk"
    
    # Test data
    test_data = {
        "prompt": "Compare cats and dogs",
        "language": "zh"
    }
    
    print(f"Testing DingTalk endpoint: {base_url}{endpoint}")
    print(f"Test data: {json.dumps(test_data, ensure_ascii=False)}")
    print("-" * 60)
    
    try:
        # Make the request
        start_time = time.time()
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60  # 60 second timeout for image generation
        )
        request_time = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {request_time:.2f} seconds")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        if response.status_code == 200:
            # Parse JSON response
            try:
                data = response.json()
                print("\n✅ SUCCESS: DingTalk endpoint working correctly!")
                print(f"Markdown: {data.get('markdown', 'N/A')}")
                print(f"Image URL: {data.get('image_url', 'N/A')}")
                print(f"Filename: {data.get('filename', 'N/A')}")
                print(f"Graph Type: {data.get('graph_type', 'N/A')}")
                print(f"Prompt: {data.get('prompt', 'N/A')}")
                print(f"Language: {data.get('language', 'N/A')}")
                
                # Check timing information
                timing = data.get('timing', {})
                if timing:
                    print(f"\nTiming Information:")
                    print(f"  LLM Time: {timing.get('llm_time', 'N/A')}s")
                    print(f"  Render Time: {timing.get('render_time', 'N/A')}s")
                    print(f"  Total Time: {timing.get('total_time', 'N/A')}s")
                
                # Test if the image URL is accessible
                print(f"\nTesting image accessibility...")
                img_response = requests.head(data.get('image_url', ''), timeout=10)
                if img_response.status_code == 200:
                    print(f"✅ Image accessible: {img_response.headers.get('Content-Type', 'Unknown')}")
                else:
                    print(f"❌ Image not accessible: Status {img_response.status_code}")
                
            except json.JSONDecodeError as e:
                print(f"❌ ERROR: Failed to parse JSON response: {e}")
                print(f"Response content: {response.text[:500]}...")
                
        else:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response content: {response.text[:500]}...")
                
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (60 seconds)")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Make sure MindGraph is running on port 9527")
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
    
    print("\n" + "=" * 60)

def test_backward_compatibility():
    """Test backward compatibility route (without /api prefix)."""
    
    # Test configuration - use dynamic server URL
    try:
        from config import config
        base_url = config.SERVER_URL
    except ImportError:
        base_url = "http://localhost:9527"  # Fallback for testing
    endpoint = "/generate_dingtalk"  # Without /api prefix
    
    print(f"Testing backward compatibility: {base_url}{endpoint}")
    print("-" * 60)
    
    test_data = {
        "prompt": "Simple mind map",
        "language": "en"
    }
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Backward compatibility status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backward compatibility working!")
        else:
            print("❌ Backward compatibility failed")
            
    except Exception as e:
        print(f"❌ Backward compatibility test error: {e}")

if __name__ == "__main__":
    print("MindGraph DingTalk Endpoint Test")
    print("=" * 60)
    
    # Test main endpoint
    test_dingtalk_endpoint()
    
    # Test backward compatibility
    test_backward_compatibility()
    
    print("\nTest completed!")
    print("\nTo use in DingTalk:")
    print("1. The 'markdown' field contains the formatted image reference")
    print("2. The 'image_url' field contains the direct image URL")
    print("3. Images are stored temporarily and served via /api/temp_images/")
    print("4. Images are automatically cleaned up after 24 hours")
    print("5. Both /api/generate_dingtalk and /generate_dingtalk endpoints work")
