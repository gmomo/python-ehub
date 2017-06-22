"""
Provides some utility functions for all code in energy_hub.
"""
import functools


def cached_property(func):
    """Return a property that caches results.

    Args:
        func: The function to decorated

    Returns:
        The decorated cached property
    """
    @property
    @functools.lru_cache(maxsize=1)
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return _wrapper
