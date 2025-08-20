"""
LLM Clients for Hybrid Agent Processing

This module provides async interfaces for DeepSeek and Qwen LLM clients
used by diagram agents for layout optimization and style enhancement.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from config import config

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """Async client for DeepSeek LLM API"""
    
    def __init__(self):
        self.api_url = config.DEEPSEEK_API_URL
        self.api_key = config.DEEPSEEK_API_KEY
        self.timeout = 30  # seconds
        
    async def chat_completion(self, messages: List[Dict], temperature: float = 0.7, 
                            max_tokens: int = 1000) -> str:
        """
        Send chat completion request to DeepSeek
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response content as string
        """
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API error {response.status}: {error_text}")
                        raise Exception(f"DeepSeek API error: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.error("DeepSeek API timeout")
            raise Exception("DeepSeek API timeout")
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise


class QwenClient:
    """Async client for Qwen LLM API"""
    
    def __init__(self, model_type='classification'):
        """
        Initialize QwenClient with specific model type
        
        Args:
            model_type (str): 'classification' for qwen-turbo, 'generation' for qwen-plus
        """
        self.api_url = config.QWEN_API_URL
        self.api_key = config.QWEN_API_KEY
        self.timeout = 30  # seconds
        self.model_type = model_type
        
    async def chat_completion(self, messages: List[Dict], temperature: float = 0.7, 
                            max_tokens: int = 1000) -> str:
        """
        Send chat completion request to Qwen
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response content as string
        """
        try:
            # Select appropriate model based on task type
            if self.model_type == 'classification':
                model_name = config.QWEN_MODEL_CLASSIFICATION
            else:  # generation
                model_name = config.QWEN_MODEL_GENERATION
                
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
                # Qwen3 models require enable_thinking: False when not using streaming
                # to avoid API errors. This is automatically included in all Qwen API calls.
                "extra_body": {"enable_thinking": False}
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        error_text = await response.text()
                        logger.error(f"Qwen API error {response.status}: {error_text}")
                        raise Exception(f"Qwen API error: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.error("Qwen API timeout")
            raise Exception("Qwen API timeout")
        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            raise


# Global client instances
try:
    deepseek_client = DeepSeekClient()
    qwen_client_classification = QwenClient(model_type='classification')  # qwen-turbo
    qwen_client_generation = QwenClient(model_type='generation')         # qwen-plus
    qwen_client = qwen_client_classification  # Legacy compatibility
    logger.info("LLM clients initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize LLM clients: {e}")
    deepseek_client = None
    qwen_client = None
    qwen_client_classification = None
    qwen_client_generation = None

def get_llm_client():
    """Get an available LLM client for testing purposes."""
    # For testing, return a mock client if real clients aren't available
    if deepseek_client:
        return deepseek_client
    elif qwen_client:
        return qwen_client
    else:
        # Return a mock client for testing
        class MockLLMClient:
            def get_response(self, prompt):
                # Mock response for testing
                if "concepts" in prompt.lower():
                    return '{"topic": "Test Topic", "concepts": ["Concept 1", "Concept 2", "Concept 3"]}'
                elif "relationships" in prompt.lower():
                    return '{"relationships": [{"from": "Concept 1", "to": "Concept 2", "label": "relates to"}]}'
                else:
                    return '{"result": "mock response"}'
        return MockLLMClient() 