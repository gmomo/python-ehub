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


def constraint(*args, enabled=True):
    """
    Mark a function as a constraint of the model.

    The function that adds these constraints to the model is
    `_add_indexed_constraints`.

    Args:
        *args: The indices that the constraint is indexed by. Each element of
            each index is passed to the method.
        enabled: Is the constraint enabled? Defaults to True.

    Returns:
        The decorated function
    """
    def _wrapper(func):
        functools.wraps(func)

        func.is_constraint = True
        func.args = args
        func.enabled = enabled

        return func

    return _wrapper


def constraint_list(*, enabled=True):
    """
    Mark a function as a ConstraintList of the model.

    The function has to return a generator. ie: must use a yield in the method
    body.

    Args:
        enabled: Is the constraint enabled? Defaults to True.

    Returns:
        The decorated function
    """
    def _wrapper(func):
        functools.wraps(func)

        func.is_constraint_list = True
        func.enabled = enabled

        return func

    return _wrapper
