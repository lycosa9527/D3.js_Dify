"""
BrowserContext Pool Management for MindGraph
Provides deployment-aware browser context pool functionality following Playwright best practices

Key benefits:
- Eliminates browser startup overhead per request by reusing contexts
- Follows Playwright's official design principles for context isolation
- Flask Dev Server: Process-level singleton pool (shared across request threads)
- Gunicorn Production: Thread-based pools per worker process
- Automatic context lifecycle management and cleanup
- Prevents memory leaks and browser corruption issues
"""

import asyncio
import logging
import os
import sys
import time
import threading
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

def _detect_deployment_type() -> str:
    """
    Detect the deployment type for proper browser context pool strategy
    
    Returns:
        str: 'flask_dev', 'waitress', 'gunicorn', or 'unknown'
    """
    # Check for Waitress environment
    if os.getenv('WAITRESS_WORKER') == 'true' or os.getenv('MINDGRAPH_ENV') == 'waitress':
        return 'waitress'
    
    # Check for Gunicorn environment
    if os.getenv('GUNICORN_WORKER') == 'true' or os.getenv('MINDGRAPH_ENV') == 'production':
        return 'gunicorn'
    
    # Check command line for server types
    command_line = ' '.join(sys.argv).lower()
    if 'waitress' in command_line or 'waitress-serve' in command_line:
        return 'waitress'
    if 'gunicorn' in command_line:
        return 'gunicorn'
    
    # Check for Flask development server
    if '__main__' in os.getenv('FLASK_RUN_FROM_CLI', '') or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
        return 'flask_dev'
    elif 'app.py' in str(os.getenv('_', '')) or 'python app.py' in ' '.join(sys.argv):
        return 'flask_dev'
    else:
        # Default assumption
        return 'flask_dev'

class BrowserContextPool:
    """
    BrowserContext pool management class following Playwright best practices
    
    Features:
    - Single browser instance shared across multiple contexts
    - Pool of 5 contexts per worker for optimal concurrency
    - Automatic context creation, cleanup, and reuse
    - Context manager for safe context usage
    - Performance monitoring and statistics
    - Complete isolation between request contexts
    """
    
    def __init__(self, pool_size: int = 5):
        """
        Initialize browser context pool
        
        Args:
            pool_size: Number of contexts to maintain in the pool (default: 5)
        """
        self.pool_size = pool_size
        self.available_contexts: List[BrowserContext] = []
        self.in_use_contexts: List[BrowserContext] = []
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.initialized = False
        self._lock = threading.Lock()  # Thread safety for sync operations
        self._init_lock = None  # Will be created when needed (asyncio may not be ready)
        self.stats = {
            'total_requests': 0,
            'context_creations': 0,
            'context_reuses': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'total_startup_time_saved': 0.0,
            'last_request_time': 0.0
        }
        
        # Browser launch configuration (optimized for PNG generation)
        self.browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-ipc-flooding-protection'
        ]
    
    async def initialize(self):
        """Initialize the browser context pool with a single browser instance (THREAD-SAFE)"""
        # Quick check without lock for performance
        if self.initialized:
            return
            
        # Create async lock if needed and use it for thread-safe initialization
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
            
        async with self._init_lock:
            # Double-check inside lock
            if self.initialized:
                return
                
            logger.info(f"Initializing browser context pool with {self.pool_size} contexts...")
            init_start_time = time.time()
            
            try:
                # Initialize playwright first
                if not self.playwright:
                    self.playwright = await async_playwright().start()
                
                # Create single browser instance
                browser_start_time = time.time()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=self.browser_args
                )
                browser_creation_time = time.time() - browser_start_time
                
                logger.info(f"Single browser instance created in {browser_creation_time:.3f}s")
                
                # Create initial pool of contexts
                context_creation_start = time.time()
                new_contexts = []
                for i in range(self.pool_size):
                    context_start_time = time.time()
                    context = await self.browser.new_context(
                        # Context configuration for optimal PNG generation
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='MindGraph PNG Generator/1.0',
                        java_script_enabled=True,
                        ignore_https_errors=True
                    )
                    context_creation_time = time.time() - context_start_time
                    
                    new_contexts.append(context)
                    logger.info(f"Context {i+1}/{self.pool_size} created in {context_creation_time:.3f}s")
                
                context_pool_time = time.time() - context_creation_start
                
                # Update state atomically under regular lock
                with self._lock:
                    self.available_contexts.extend(new_contexts)
                    self.stats['context_creations'] += len(new_contexts)
                    # Mark as initialized LAST, after everything is ready
                    self.initialized = True
                
                total_init_time = time.time() - init_start_time
                logger.info(f"Browser context pool initialized successfully in {total_init_time:.3f}s")
                logger.info(f"Context pool creation took {context_pool_time:.3f}s")
                
                # Verify pool health after initialization
                await self.cleanup_invalid_contexts()
                
            except Exception as e:
                logger.error(f"Failed to initialize browser context pool: {e}")
                # Clean up any partially created contexts
                if 'new_contexts' in locals():
                    for context in new_contexts:
                        try:
                            await context.close()
                        except:
                            pass
                        
                # Reset state on failure
                with self._lock:
                    self.initialized = False
                    self.available_contexts.clear()
                    
                if self.browser:
                    try:
                        await self.browser.close()
                    except:
                        pass
                    self.browser = None
                    
                if self.playwright:
                    try:
                        await self.playwright.stop()
                    except:
                        pass
                    self.playwright = None
                    
                raise
    
    @asynccontextmanager
    async def get_context(self):
        """
        Context manager to get a browser context from the pool
        
        Usage:
            async with browser_context_pool.get_context() as context:
                page = await context.new_page()
                # ... use page ...
                # Context is automatically cleaned up and returned to pool
        """
        if not self.initialized:
            await self.initialize()
        
        request_start_time = time.time()
        context = None
        
        try:
            # Get context from pool or create new one
            with self._lock:
                logger.info(f"DEBUG: Pool state - available: {len(self.available_contexts)}, in_use: {len(self.in_use_contexts)}")
                
                if self.available_contexts:
                    context = self.available_contexts.pop()
                    logger.info(f"DEBUG: Retrieved context from pool - type: {type(context)}, id: {id(context) if context else 'None'}")
                    
                    # Validate context before using it
                    if context and hasattr(context, 'browser') and context.browser:
                        logger.info(f"DEBUG: Context validation passed - has browser: {hasattr(context, 'browser')}, browser: {context.browser}")
                        self.in_use_contexts.append(context)
                        self.stats['pool_hits'] += 1
                        self.stats['context_reuses'] += 1
                        # Each reuse saves ~4.5s of browser startup time
                        self.stats['total_startup_time_saved'] += 4.5
                        logger.info(f"Context {id(context)} retrieved from pool (pool hit)")
                    else:
                        # Invalid context, create new one
                        logger.warning(f"DEBUG: Invalid context in pool - context: {context}, has browser: {hasattr(context, 'browser') if context else 'N/A'}")
                        self.stats['pool_misses'] += 1
                        context = None
                else:
                    # Pool exhausted - create new context
                    logger.info("Pool exhausted, creating new context")
                    self.stats['pool_misses'] += 1
            
            if not context:
                                # Create new context outside the lock
                logger.info("DEBUG: Creating new browser context...")
                context_creation_start = time.time()
                context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='MindGraph PNG Generator/1.0',
                    java_script_enabled=True,
                    ignore_https_errors=True
                )
                context_creation_time = time.time() - context_creation_start
                
                logger.info(f"DEBUG: New context created - type: {type(context)}, id: {id(context)}, time: {context_creation_time:.3f}s")
                logger.info(f"DEBUG: New context attributes - has _impl_obj: {hasattr(context, '_impl_obj')}, has browser: {hasattr(context, 'browser')}")
                
                with self._lock:
                    self.in_use_contexts.append(context)
                    self.stats['context_creations'] += 1
                
                logger.info(f"New context {id(context)} created in {context_creation_time:.3f}s")
            
            # Final validation before yielding
            logger.info(f"DEBUG: Final validation - context: {context}, type: {type(context) if context else 'None'}")
            if context:
                logger.info(f"DEBUG: Final validation - has browser: {hasattr(context, 'browser')}, browser: {getattr(context, 'browser', 'No browser')}")
                logger.info(f"DEBUG: Final validation - has _impl_obj: {hasattr(context, '_impl_obj')}")
            
            if not context or not hasattr(context, 'browser') or not context.browser:
                logger.error(f"DEBUG: Final validation failed - context: {context}, has browser: {hasattr(context, 'browser') if context else 'N/A'}")
                raise Exception("Failed to create or retrieve valid browser context")
            
            # Additional Playwright-specific validation
            if not hasattr(context, '_impl_obj'):
                logger.error(f"DEBUG: Playwright validation failed - missing _impl_obj attribute")
                raise Exception("Browser context is missing required Playwright attributes")
            
            logger.info(f"DEBUG: Final validation passed - context {id(context)} is ready for use")
            
            # Update stats
            request_time = time.time() - request_start_time
            with self._lock:
                self.stats['total_requests'] += 1
                self.stats['last_request_time'] = request_time
            
            yield context
            
        finally:
            # Return context to pool with proper cleanup
            if context:
                logger.info(f"DEBUG: Starting context cleanup for context {id(context)}")
                logger.info(f"DEBUG: Context state before cleanup - type: {type(context)}, has browser: {hasattr(context, 'browser')}")
                
                # Clean up context state before returning to pool
                try:
                    # Close all pages in the context (this is safe)
                    pages = context.pages
                    logger.info(f"DEBUG: Closing {len(pages)} pages in context")
                    for page in pages:
                        try:
                            await page.close()
                        except Exception as e:
                            logger.warning(f"Error closing page in context {id(context)}: {e}")
                    
                    # Skip problematic cleanup operations that can corrupt the context
                    # await context.clear_cookies()  # This can corrupt the context
                    # await context.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")  # This can also cause issues
                        
                except Exception as e:
                    logger.warning(f"Error during context cleanup: {e}")
                
                logger.info(f"DEBUG: Context cleanup completed for context {id(context)}")
                logger.info(f"Returning context {id(context)} to pool")
                
                # Return context to pool if it's still healthy
                with self._lock:
                    logger.info(f"DEBUG: Validating context {id(context)} for pool return")
                    if context in self.in_use_contexts:
                        self.in_use_contexts.remove(context)
                        logger.info(f"DEBUG: Context {id(context)} removed from in_use list")
                    
                    # Check if context is still connected and pool has space
                    try:
                        # Validate context is still usable
                        logger.info(f"DEBUG: Context validation - context: {context}, has browser: {hasattr(context, 'browser') if context else 'N/A'}")
                        
                        if (context and 
                            hasattr(context, 'browser') and 
                            context.browser and 
                            len(self.available_contexts) < self.pool_size):
                            
                            logger.info(f"DEBUG: Context basic validation passed")
                            
                            # Basic validation: check if context has required attributes
                            if (hasattr(context, '_impl_obj') and 
                                hasattr(context, 'browser') and 
                                context.browser):
                                
                                logger.info(f"DEBUG: Context full validation passed, returning to pool")
                                # Context appears healthy, return to pool
                                self.available_contexts.append(context)
                                logger.info(f"Context {id(context)} returned to pool. Available: {len(self.available_contexts)}")
                                
                            else:
                                logger.warning(f"DEBUG: Context {id(context)} failed full validation - _impl_obj: {hasattr(context, '_impl_obj')}, browser: {hasattr(context, 'browser')}")
                                # Context is unhealthy, close it
                                try:
                                    await context.close()
                                except:
                                    pass
                        else:
                            logger.warning(f"DEBUG: Context {id(context)} failed basic validation")
                            # Pool full or context disconnected - close it
                            logger.info(f"Context {id(context)} closed (pool full or disconnected)")
                            try:
                                await context.close()
                            except:
                                pass
                    except Exception as e:
                        logger.warning(f"Error checking context health: {e}")
                        try:
                            await context.close()
                        except:
                            pass
                
                # Verification log
                with self._lock:
                    logger.info(f"Final pool state - Available: {len(self.available_contexts)}, In-use: {len(self.in_use_contexts)}")
                    # Additional debug info
                    if self.available_contexts:
                        for i, ctx in enumerate(self.available_contexts):
                            logger.info(f"DEBUG: Available context {i+1}: {type(ctx)}, id: {id(ctx) if ctx else 'None'}, has browser: {hasattr(ctx, 'browser') if ctx else 'N/A'}")
                    if self.in_use_contexts:
                        for i, ctx in enumerate(self.in_use_contexts):
                            logger.info(f"DEBUG: In-use context {i+1}: {type(ctx)}, id: {id(ctx) if ctx else 'None'}, has browser: {hasattr(ctx, 'browser') if ctx else 'N/A'}")
    
    async def reset_pool(self):
        """Reset the context pool by cleaning up and recreating contexts"""
        logger.warning("Resetting browser context pool...")
        
        # Collect all context references
        with self._lock:
            all_contexts = list(self.in_use_contexts) + list(self.available_contexts)
            self.available_contexts.clear()
            self.in_use_contexts.clear()
        
        # Close all contexts
        for context in all_contexts:
            try:
                if context and hasattr(context, 'browser') and context.browser:
                    await context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
        
        # Recreate context pool
        if self.browser:
            await self._create_fresh_contexts()
            
        logger.info("Browser context pool reset and reinitialized")
    
    async def cleanup_invalid_contexts(self):
        """Remove invalid contexts from the pool"""
        logger.info("Cleaning up invalid contexts from pool...")
        
        with self._lock:
            # Clean available contexts
            valid_available = []
            for context in self.available_contexts:
                if context and hasattr(context, 'browser') and context.browser:
                    valid_available.append(context)
                else:
                    logger.warning(f"Removing invalid context {id(context) if context else 'None'} from available pool")
                    try:
                        if context:
                            await context.close()
                    except:
                        pass
            
            # Clean in-use contexts
            valid_in_use = []
            for context in self.in_use_contexts:
                if context and hasattr(context, 'browser') and context.browser:
                    valid_in_use.append(context)
                else:
                    logger.warning(f"Removing invalid context {id(context) if context else 'None'} from in-use pool")
                    try:
                        if context:
                            await context.close()
                    except:
                        pass
            
            # Update pools
            self.available_contexts = valid_available
            self.in_use_contexts = valid_in_use
            
            logger.info(f"Pool cleanup completed. Valid available: {len(valid_available)}, Valid in-use: {len(valid_in_use)}")
    
    async def _create_fresh_contexts(self):
        """Create fresh contexts for the pool"""
        if not self.browser:
            return
            
        logger.info(f"Creating {self.pool_size} fresh contexts...")
        new_contexts = []
        
        for i in range(self.pool_size):
            try:
                context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='MindGraph PNG Generator/1.0',
                    java_script_enabled=True,
                    ignore_https_errors=True
                )
                new_contexts.append(context)
                logger.debug(f"Fresh context {i+1}/{self.pool_size} created")
            except Exception as e:
                logger.error(f"Failed to create fresh context {i+1}: {e}")
                break
        
        # Add contexts to pool
        if new_contexts:
            with self._lock:
                self.available_contexts.extend(new_contexts)
                self.stats['context_creations'] += len(new_contexts)
                logger.info(f"Added {len(new_contexts)} fresh contexts to pool")

    async def cleanup(self):
        """Clean up all contexts and browser instance"""
        logger.info("Cleaning up browser context pool...")
        
        with self._lock:
            # Close all contexts
            all_contexts = list(self.in_use_contexts) + list(self.available_contexts)
            self.available_contexts.clear()
            self.in_use_contexts.clear()
        
        for context in all_contexts:
            try:
                await context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
        
        # Close browser
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        # Stop playwright
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
        
        # Reset state
        with self._lock:
            self.browser = None
            self.playwright = None
            self.initialized = False
        
        logger.info("Browser context pool cleanup completed")
    
    def get_stats(self) -> dict:
        """Get browser context pool performance statistics (thread-safe)"""
        with self._lock:
            pool_efficiency = (self.stats['pool_hits'] / max(self.stats['total_requests'], 1)) * 100
            avg_startup_time_saved = self.stats['total_startup_time_saved'] / max(self.stats['total_requests'], 1)
            
            # Get counts safely
            available_count = len(self.available_contexts)
            in_use_count = len(self.in_use_contexts)
            total_count = available_count + in_use_count
            
            # Validate contexts in pool
            valid_available = sum(1 for ctx in self.available_contexts if ctx and hasattr(ctx, 'browser') and ctx.browser)
            valid_in_use = sum(1 for ctx in self.in_use_contexts if ctx and hasattr(ctx, 'browser') and ctx.browser)
            
            return {
                'pool_size': self.pool_size,
                'available_contexts': available_count,
                'in_use_contexts': in_use_count,
                'total_contexts': total_count,
                'valid_available_contexts': valid_available,
                'valid_in_use_contexts': valid_in_use,
                'initialized': self.initialized,
                'browser_connected': self.browser is not None and hasattr(self.browser, '_is_connected') and self.browser._is_connected(),
                'stats': {
                    'total_requests': self.stats['total_requests'],
                    'context_creations': self.stats['context_creations'],
                    'context_reuses': self.stats['context_reuses'],
                    'pool_hits': self.stats['pool_hits'],
                    'pool_misses': self.stats['pool_misses'],
                    'pool_efficiency_percent': round(pool_efficiency, 1),
                    'total_startup_time_saved_seconds': round(self.stats['total_startup_time_saved'], 1),
                    'average_startup_time_saved_per_request': round(avg_startup_time_saved, 3),
                    'last_request_time_seconds': round(self.stats['last_request_time'], 3)
                }
            }

# Deployment-aware browser context pool management
_deployment_type = _detect_deployment_type()
_global_pool_lock = threading.Lock()

# Flask Development Server: Process-level singleton pool (shared across request threads)
_flask_singleton_pool: Optional[BrowserContextPool] = None

def get_browser_context_pool() -> BrowserContextPool:
    """
    Get the appropriate browser context pool instance based on deployment type
    
    Returns:
        BrowserContextPool: The browser context pool instance (singleton for Flask dev, per-worker for Gunicorn)
    """
    global _flask_singleton_pool
    
    if _deployment_type == 'flask_dev':
        # Flask Development Server: Use process-level singleton pool
        if _flask_singleton_pool is None:
            with _global_pool_lock:
                # Double-check locking pattern
                if _flask_singleton_pool is None:
                    logger.info(f"Creating singleton browser context pool for Flask development server (process-level shared pool)")
                    _flask_singleton_pool = BrowserContextPool(pool_size=5)
        
        return _flask_singleton_pool
    
    elif _deployment_type == 'waitress':
        # Waitress Production: Use process-level singleton pool (Waitress uses thread pooling)
        if _flask_singleton_pool is None:
            with _global_pool_lock:
                # Double-check locking pattern  
                if _flask_singleton_pool is None:
                    logger.info(f"Creating singleton browser context pool for Waitress server (process-level shared pool)")
                    _flask_singleton_pool = BrowserContextPool(pool_size=5)
        
        return _flask_singleton_pool
    
    elif _deployment_type == 'gunicorn':
        # Gunicorn Production: Use process-level singleton pool (Gunicorn workers are processes, not threads)
        if _flask_singleton_pool is None:
            with _global_pool_lock:
                # Double-check locking pattern
                if _flask_singleton_pool is None:
                    worker_id = os.getenv('GUNICORN_WORKER_ID', 'unknown')
                    process_id = os.getpid()
                    logger.info(f"Creating singleton browser context pool for Gunicorn worker {worker_id} (process {process_id})")
                    _flask_singleton_pool = BrowserContextPool(pool_size=5)
        
        return _flask_singleton_pool
    
    else:
        # Fallback: Default to Flask dev behavior
        logger.warning(f"Unknown deployment type '{_deployment_type}', defaulting to singleton pool")
        if _flask_singleton_pool is None:
            with _global_pool_lock:
                if _flask_singleton_pool is None:
                    _flask_singleton_pool = BrowserContextPool(pool_size=5)
        return _flask_singleton_pool

async def initialize_worker_browser_context_pool():
    """Initialize browser context pool for the current worker"""
    pool = get_browser_context_pool()
    await pool.initialize()
    logger.info("Worker browser context pool initialized")

async def cleanup_worker_browser_context_pool():
    """Cleanup browser context pool for the current deployment type"""
    global _flask_singleton_pool
    
    if _deployment_type == 'flask_dev':
        # Flask Development Server: Cleanup singleton pool
        if _flask_singleton_pool:
            with _global_pool_lock:
                if _flask_singleton_pool:
                    await _flask_singleton_pool.cleanup()
                    _flask_singleton_pool = None
                    logger.info("Flask development server browser context pool cleaned up")
    
    elif _deployment_type == 'waitress':
        # Waitress Production: Cleanup singleton pool
        if _flask_singleton_pool:
            with _global_pool_lock:
                if _flask_singleton_pool:
                    await _flask_singleton_pool.cleanup()
                    _flask_singleton_pool = None
                    logger.info("Waitress server browser context pool cleaned up")
    
    elif _deployment_type == 'gunicorn':
        # Gunicorn Production: Cleanup singleton pool (same as Flask/Waitress)
        if _flask_singleton_pool:
            with _global_pool_lock:
                if _flask_singleton_pool:
                    await _flask_singleton_pool.cleanup()
                    _flask_singleton_pool = None
                    worker_id = os.getenv('GUNICORN_WORKER_ID', 'unknown')
                    process_id = os.getpid()
                    logger.info(f"Gunicorn worker {worker_id} (process {process_id}) browser context pool cleaned up")

def cleanup_browser_context_pool_sync():
    """Synchronous cleanup for Flask development server (safe to call anytime)"""
    global _flask_singleton_pool
    
    if _deployment_type == 'flask_dev' and _flask_singleton_pool:
        try:
            import asyncio
            # Use a simple approach for Flask dev cleanup
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_flask_singleton_pool.cleanup())
                with _global_pool_lock:
                    _flask_singleton_pool = None
                logger.info("Flask browser context pool manually cleaned up")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error during manual Flask cleanup: {e}")
    else:
        logger.debug("No Flask browser context pool to clean up")

def get_browser_context_pool_stats() -> dict:
    """Get browser context pool statistics for monitoring"""
    global _flask_singleton_pool
    thread_id = threading.get_ident()
    
    if _deployment_type == 'flask_dev':
        # Flask Development Server: Get singleton pool stats
        if _flask_singleton_pool:
            current_stats = _flask_singleton_pool.get_stats()
        else:
            current_stats = _get_empty_stats()
        
        # Add deployment information
        current_stats['deployment_info'] = {
            'deployment_type': 'flask_dev',
            'pool_strategy': 'process_singleton',
            'current_thread_id': thread_id,
            'total_pools': 1 if _flask_singleton_pool else 0,
            'description': 'Single shared pool for all request threads'
        }
    
    elif _deployment_type == 'waitress':
        # Waitress Production: Get singleton pool stats
        if _flask_singleton_pool:
            current_stats = _flask_singleton_pool.get_stats()
        else:
            current_stats = _get_empty_stats()
        
        # Add deployment information
        current_stats['deployment_info'] = {
            'deployment_type': 'waitress',
            'pool_strategy': 'process_singleton',
            'current_thread_id': thread_id,
            'total_pools': 1 if _flask_singleton_pool else 0,
            'description': 'Single shared pool for all Waitress threads'
        }
    
    elif _deployment_type == 'gunicorn':
        # Gunicorn Production: Get singleton pool stats (same as Flask/Waitress)
        if _flask_singleton_pool:
            current_stats = _flask_singleton_pool.get_stats()
        else:
            current_stats = _get_empty_stats()
        
        # Add deployment information
        current_stats['deployment_info'] = {
            'deployment_type': 'gunicorn',
            'pool_strategy': 'process_singleton',
            'current_thread_id': thread_id,
            'total_pools': 1 if _flask_singleton_pool else 0,
            'worker_id': os.getenv('GUNICORN_WORKER_ID', 'unknown'),
            'process_id': os.getpid(),
            'description': 'Single shared pool per Gunicorn worker process'
        }
    
    else:
        # Unknown deployment type
        current_stats = _get_empty_stats()
        current_stats['deployment_info'] = {
            'deployment_type': _deployment_type,
            'pool_strategy': 'unknown',
            'current_thread_id': thread_id,
            'total_pools': 0,
            'description': 'Unknown deployment configuration'
        }
    
    return current_stats

def _get_empty_stats() -> dict:
    """Get empty stats structure for when no pool exists"""
    return {
        'pool_size': 0,
        'available_contexts': 0,
        'in_use_contexts': 0,
        'total_contexts': 0,
        'initialized': False,
        'stats': {
            'total_requests': 0,
            'context_creations': 0,
            'context_reuses': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'pool_efficiency_percent': 0.0,
            'total_startup_time_saved_seconds': 0.0,
            'average_startup_time_saved_per_request': 0.0,
            'last_request_time_seconds': 0.0
        }
    }

# Note: All functions now use the BrowserContext pool approach
# This follows Playwright's official best practices for context isolation

# Worker lifecycle management
import atexit

def setup_worker_cleanup():
    """Setup cleanup handlers for worker shutdown"""
    def cleanup_on_exit():
        """Synchronous cleanup for atexit handler"""
        try:
            import asyncio
            # Create new event loop for cleanup (safer approach)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(cleanup_worker_browser_context_pool())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error during worker cleanup: {e}")
    
    # Register cleanup handler
    atexit.register(cleanup_on_exit)

# Auto-setup cleanup when module is imported (disabled for Flask dev to prevent deadlocks)
deployment_type = _detect_deployment_type()
if deployment_type == 'gunicorn':
    # Enable automatic cleanup for Gunicorn workers only
    setup_worker_cleanup()
    logger.info("Browser context pool cleanup handler registered for Gunicorn worker")
elif deployment_type == 'waitress':
    # Waitress uses singleton pool like Flask dev - no automatic cleanup to avoid threading conflicts
    logger.info("Browser context pool cleanup handler disabled for Waitress server (singleton pool, manual cleanup)")
else:
    # Flask dev server: manual cleanup to avoid threading conflicts
    logger.info("Browser context pool cleanup handler disabled for Flask dev server (manual cleanup)")
