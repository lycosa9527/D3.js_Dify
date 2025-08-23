#!/usr/bin/env python3
"""
DingTalk Integration Example for MindGraph

This example shows how to use the new /api/generate_dingtalk endpoint
to generate images and send them to DingTalk using markdown format.

The key difference from the regular PNG endpoint is that this returns
markdown format with image URLs instead of binary PNG data.
"""

import requests
import json
import time

class DingTalkMindGraphBot:
    """DingTalk bot that integrates with MindGraph for image generation."""
    
    def __init__(self, mindgraph_url=None):
        """
        Initialize the DingTalk MindGraph bot.
        
        Args:
            mindgraph_url: Base URL of the MindGraph server (auto-detected if None)
        """
        if mindgraph_url is None:
            try:
                from config import config
                mindgraph_url = config.SERVER_URL
            except ImportError:
                mindgraph_url = "http://localhost:9527"  # Fallback for testing
        self.mindgraph_url = mindgraph_url.rstrip('/')
        self.dingtalk_webhook = None  # Set this to your DingTalk webhook URL
        
    def generate_mindmap(self, prompt, language="zh"):
        """
        Generate a mindmap using MindGraph's DingTalk endpoint.
        
        Args:
            prompt: Text description of what to visualize
            language: Language code ('zh' for Chinese, 'en' for English)
            
        Returns:
            dict: Response containing markdown and image URL
        """
        endpoint = f"{self.mindgraph_url}/api/generate_dingtalk"
        
        data = {
            "prompt": prompt,
            "language": language
        }
        
        try:
            print(f"Generating mindmap for prompt: {prompt}")
            print(f"Language: {language}")
            
            response = requests.post(
                endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mindmap generated successfully!")
                print(f"Graph type: {result.get('graph_type')}")
                print(f"Image URL: {result.get('image_url')}")
                print(f"Markdown: {result.get('markdown')}")
                return result
            else:
                error_msg = f"Failed to generate mindmap: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', 'Unknown error')}"
                except:
                    pass
                print(f"❌ {error_msg}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
            return None
        except Exception as e:
            print(f"❌ Error generating mindmap: {e}")
            return None
    
    def send_dingtalk_message(self, webhook_url, markdown_text, title="MindGraph Generated", at_user_ids=None):
        """
        Send a markdown message to DingTalk.
        
        Args:
            webhook_url: DingTalk webhook URL
            markdown_text: Markdown content (including the image)
            title: Message title
            at_user_ids: List of user IDs to @mention
        """
        # This is a simplified example - in real usage you'd use the DingTalk SDK
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": markdown_text
            }
        }
        
        if at_user_ids:
            message["at"] = {
                "atUserIds": at_user_ids,
                "isAtAll": False
            }
        
        try:
            response = requests.post(
                webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print(f"✅ Message sent to DingTalk successfully!")
                else:
                    print(f"❌ DingTalk API error: {result.get('errmsg', 'Unknown error')}")
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending DingTalk message: {e}")
    
    def process_dingtalk_request(self, request_data):
        """
        Process a DingTalk webhook request and generate/send mindmap.
        
        Args:
            request_data: Data from DingTalk webhook
        """
        try:
            # Extract information from DingTalk request
            text_content = request_data.get('text', {}).get('content', '').strip()
            user_id = request_data.get('senderStaffId', '')
            session_webhook = request_data.get('sessionWebhook', '')
            
            print(f"Processing DingTalk request:")
            print(f"  Content: {text_content}")
            print(f"  User ID: {user_id}")
            print(f"  Session Webhook: {session_webhook}")
            
            # Check if this is a mindmap request
            if text_content.lower() in ['mindmap', '思维导图', '图表', 'graph']:
                # Generate mindmap
                result = self.generate_mindmap(
                    prompt="Create a mindmap about artificial intelligence",
                    language="zh"
                )
                
                if result and session_webhook:
                    # Send to DingTalk
                    markdown_text = f"@{user_id}  \n  {result['markdown']}"
                    self.send_dingtalk_message(
                        webhook_url=session_webhook,
                        markdown_text=markdown_text,
                        title="AI Mindmap Generated",
                        at_user_ids=[user_id] if user_id else None
                    )
                else:
                    print("❌ Failed to generate or send mindmap")
            else:
                print(f"Not a mindmap request: {text_content}")
                
        except Exception as e:
            print(f"❌ Error processing DingTalk request: {e}")

def example_usage():
    """Example usage of the DingTalk MindGraph bot."""
    
    print("DingTalk MindGraph Integration Example")
    print("=" * 50)
    
    # Initialize the bot
    bot = DingTalkMindGraphBot()
    
    # Example 1: Generate a mindmap
    print("\n1. Generating a mindmap...")
    result = bot.generate_mindmap(
        prompt="Compare traditional education vs online learning",
        language="zh"
    )
    
    if result:
        print(f"\nGenerated markdown for DingTalk:")
        print(f"{result['markdown']}")
        
        # Example 2: Show how to use in DingTalk
        print(f"\n2. To use in DingTalk, send this markdown:")
        print(f"   {result['markdown']}")
        
        # Example 3: Show the image URL
        print(f"\n3. Direct image URL:")
        print(f"   {result['image_url']}")
    
    print("\n" + "=" * 50)
    print("Integration Notes:")
    print("- The /api/generate_dingtalk endpoint returns JSON, not PNG")
    print("- Use the 'markdown' field directly in DingTalk messages")
    print("- Images are stored in /static/images/ and served by Flask")
    print("- Both endpoints work: /api/generate_dingtalk and /generate_dingtalk")

if __name__ == "__main__":
    example_usage()
