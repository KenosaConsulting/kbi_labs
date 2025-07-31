"""Circuit Breaker Pattern Implementation"""
from typing import Type, Optional
import asyncio

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Optional[Type[Exception]] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception or Exception
        self.failure_count = 0
        self.is_open = False
    
    async def __aenter__(self):
        if self.is_open:
            raise Exception("Circuit breaker is open")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.expected_exception):
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                # Reset after recovery timeout
                asyncio.create_task(self._reset_after_timeout())
        return False
    
    async def _reset_after_timeout(self):
        await asyncio.sleep(self.recovery_timeout)
        self.is_open = False
        self.failure_count = 0
