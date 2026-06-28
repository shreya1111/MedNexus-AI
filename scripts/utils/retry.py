"""
Retry utilities for MedNexus-AI Knowledge Ingestion Framework.

Provides retry logic with exponential backoff for handling transient failures.
"""

import time
import functools
from typing import Callable, TypeVar, Optional, Type, Tuple
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be at least 1")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True,
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_multiplier: Multiplier for delay between retries
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch
        log_errors: Whether to log retry attempts
        
    Returns:
        Decorated function
        
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def download_file(url):
            # Download logic
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        if log_errors:
                            logger.error(
                                f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise
                    
                    if log_errors:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                    
                    time.sleep(delay)
                    delay = min(delay * backoff_multiplier, max_delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RetryManager:
    """Manager for retry operations with detailed tracking."""
    
    def __init__(self, config: RetryConfig):
        """
        Initialize retry manager.
        
        Args:
            config: Retry configuration
        """
        self.config = config
        self.attempts = 0
        self.total_delay = 0.0
    
    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        delay = self.config.initial_delay
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.attempts = attempt
            
            try:
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(
                        f"Function {func.__name__} succeeded on attempt {attempt}"
                    )
                
                return result
                
            except self.config.exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_attempts:
                    logger.error(
                        f"Function {func.__name__} failed after {self.config.max_attempts} attempts"
                    )
                    raise
                
                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                
                time.sleep(delay)
                self.total_delay += delay
                delay = min(delay * self.config.backoff_multiplier, self.config.max_delay)
        
        if last_exception:
            raise last_exception
    
    def reset(self) -> None:
        """Reset retry statistics."""
        self.attempts = 0
        self.total_delay = 0.0
    
    def get_stats(self) -> dict:
        """
        Get retry statistics.
        
        Returns:
            Dictionary with retry stats
        """
        return {
            "attempts": self.attempts,
            "total_delay_seconds": self.total_delay,
            "max_attempts": self.config.max_attempts,
            "succeeded": self.attempts < self.config.max_attempts,
        }


def retry_on_exception(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    Execute a function with retry logic (functional style).
    
    Args:
        func: Function to execute
        config: Retry configuration (uses defaults if None)
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
        
    Returns:
        Function result
    """
    if config is None:
        config = RetryConfig()
    
    manager = RetryManager(config)
    return manager.execute(func, *args, **kwargs)


class Retryable:
    """
    Context manager for retryable operations.
    
    Example:
        with Retryable(max_attempts=3) as retry:
            result = retry.attempt(download_file, url)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_delay: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """Initialize retryable context."""
        self.config = RetryConfig(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            backoff_multiplier=backoff_multiplier,
            max_delay=max_delay,
            exceptions=exceptions,
        )
        self.manager = RetryManager(self.config)
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        return False
    
    def attempt(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Attempt to execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        return self.manager.execute(func, *args, **kwargs)
    
    def stats(self) -> dict:
        """Get retry statistics."""
        return self.manager.get_stats()
