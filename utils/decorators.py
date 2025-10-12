"""
Decorators for HPC-ScaleTest framework.
"""

import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def run_before(*methods: str):
    """
    Decorator that ensures specified methods are run before the decorated method.
    
    Args:
        *methods: Names of methods to run before the decorated method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # Run the specified methods first
            for method_name in methods:
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    if callable(method):
                        logger.debug(f"Running '{method_name}' before '{func.__name__}'")
                        method()
                    else:
                        logger.warning(f"Method '{method_name}' is not callable")
                else:
                    logger.warning(f"Method '{method_name}' not found in class")
            
            # Then run the actual function
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def check_binary_and_compile(func: Callable) -> Callable:
    """
    Decorator that checks if binary exists and compiles if needed before running the function.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        # Check if we have a test runner instance with a test
        if hasattr(self, 'test') and hasattr(self, '_check_and_build_binary'):
            logger.debug("Checking for binary and compiling if needed")
            self._check_and_build_binary()
        
        # Run the actual function
        return func(self, *args, **kwargs)
    return wrapper