# utils/rate_limiter.py

import asyncio
import time
from typing import Optional


class RateLimiter:
    def __init__(self, calls_per_second: int = 10):
        self.calls_per_second = calls_per_second
        self.last_reset = time.time()
        self.calls = 0
        self._lock = asyncio.Lock()
    async def acquire(self):
        """Control the rate of API calls"""
        async with self._lock:
            current_time = time.time()
            if current_time - self.last_reset >= 1:
                self.calls = 0
                self.last_reset = current_time

            if self.calls >= self.calls_per_second:
                wait_time = 1 - (current_time - self.last_reset)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self.calls = 0
                self.last_reset = time.time()

            self.calls += 1

# utils/decorators.py

import asyncio
import random
from functools import wraps
from typing import TypeVar, Callable, Any

T = TypeVar('T')

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_count = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if retry_count == retries:
                        raise e
                    wait_time = (backoff_in_seconds * (2 ** retry_count)) + random.uniform(0, 1)
                    print(f"Attempt {retry_count + 1} failed. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
        return wrapper
    return decorator