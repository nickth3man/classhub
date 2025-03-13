"""Performance monitoring utilities."""
import time
import functools
import logging
from typing import Callable, Any, Dict
from dataclasses import dataclass
from datetime import datetime
import threading
from collections import defaultdict

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time: float
    memory_usage: float
    timestamp: datetime
    context: Dict[str, Any]

class PerformanceMonitor:
    """Performance monitoring system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._metrics = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_metric(self, operation: str, metrics: PerformanceMetrics) -> None:
        """Record performance metrics for an operation."""
        with self._lock:
            self._metrics[operation].append(metrics)
            if len(self._metrics[operation]) > 1000:  # Prevent memory leaks
                self._metrics[operation] = self._metrics[operation][-1000:]
    
    def get_metrics(self, operation: str) -> list[PerformanceMetrics]:
        """Get metrics for specific operation."""
        with self._lock:
            return self._metrics.get(operation, [])
    
    def get_average_execution_time(self, operation: str) -> float:
        """Calculate average execution time for an operation."""
        metrics = self.get_metrics(operation)
        if not metrics:
            return 0.0
        return sum(m.execution_time for m in metrics) / len(metrics)
    
    def clear_metrics(self, operation: str = None) -> None:
        """Clear metrics for specific or all operations."""
        with self._lock:
            if operation:
                self._metrics.pop(operation, None)
            else:
                self._metrics.clear()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def measure_performance(operation: str = None):
    """Decorator to measure function performance."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            start_memory = get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                end_memory = get_memory_usage()
                
                metrics = PerformanceMetrics(
                    execution_time=end_time - start_time,
                    memory_usage=end_memory - start_memory,
                    timestamp=datetime.now(),
                    context={'args': args, 'kwargs': kwargs}
                )
                
                op_name = operation or func.__name__
                performance_monitor.record_metric(op_name, metrics)
        
        return wrapper
    return decorator

def get_memory_usage() -> float:
    """Get current memory usage."""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # Convert to MB