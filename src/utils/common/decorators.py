"""
Reusable decorators for resilience: retry and timeout.
"""

import asyncio
import functools
import time
from typing import Callable, Type, Tuple


def retry(
    exceptions: Tuple[Type[BaseException], ...],
    attempts: int = 3,
    delay_seconds: float = 0.5,
    backoff: float = 2.0
) -> Callable:
    """Retry an async function on given exceptions with exponential backoff."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tries = attempts
            current_delay = delay_seconds
            last_exc = None
            while tries > 0:
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    tries -= 1
                    if tries <= 0:
                        break
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            if last_exc:
                raise last_exc
        return wrapper
    return decorator


def timeout(seconds: float) -> Callable:
    """Timeout an async function after given seconds."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator

